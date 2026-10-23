"""Modelos de potencia esperada (dataset A horario) y sus métricas. Usado por 03, 04 y la app."""
import numpy as np
import pandas as pd
import pvlib
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.features import agregar_features_tiempo, features_escenario, limpiar_pvod

FEATURES = ["poa", "temp_celda", "kt", "frac_difusa", "sol_zenit_deg", "sol_azimut_deg",
            "hora_sin", "hora_cos", "doy_sin", "doy_cos"]
TIPOS = ["fisico", "ridge", "rf", "xgb"]
# Plantas fuera del entrenamiento (ver docs/plan_modelado.md):
#   station04: ficha imposible (25,7 MW con 20,06 MWp de módulos).
#   station09: bajo rendimiento real -> caso de prueba del detector, no "normal".
EXCLUIDAS = ["station04", "station09"]
GAMMA_PDC = -0.004  # coef. de temperatura típico de silicio cristalino (1/°C), supuesto de la línea base


def preparar(df: pd.DataFrame, escenario: str) -> pd.DataFrame:
    """Dataset A horario -> horas de sol con features del escenario y banderas de limpieza."""
    d = limpiar_pvod(df)
    d = features_escenario(d, escenario)
    d = agregar_features_tiempo(d, "timestamp_local_utc8")
    d = d[d["is_daylight"] == 1].copy()
    d["mes_id"] = d["timestamp_local_utc8"].dt.to_period("M").astype(str)
    # Apagón: mucho sol y casi nada de potencia (A.8 del EDA). Es falla, no comportamiento normal.
    d["apagon"] = (d["poa"] > 500) & (d["pvod_power_norm"] < 0.05)
    return d


def filas_entrenamiento(d: pd.DataFrame) -> pd.Series:
    return ~d["plant_id"].isin(EXCLUIDAS) & ~d["dato_congelado"] & ~d["apagon"]


class ModeloPotencia:
    """Predice `pvod_power_norm` (potencia / capacidad) en horas de sol.

    tipo: "fisico" (PVWatts de pvlib con un k por planta), "ridge", "rf" o "xgb".
    con_planta=True agrega la planta como variable (aprende el nivel y la estacionalidad de
    cada una). Con False es un modelo "planta típica", para plantas que no estuvieron en el
    entrenamiento (station09).
    """

    def __init__(self, tipo: str, escenario: str, con_planta: bool = True, semilla: int = 0):
        if tipo not in TIPOS:
            raise ValueError(f"tipo debe ser uno de {TIPOS}")
        self.tipo, self.escenario, self.con_planta, self.semilla = tipo, escenario, con_planta, semilla

    def _matriz(self, d):
        X = d[FEATURES].fillna(0).astype(float)
        if self.con_planta:
            dummies = pd.get_dummies(d["plant_id"]).reindex(columns=self.plantas_, fill_value=0).astype(float)
            X = pd.concat([X, dummies.add_prefix("p_")], axis=1)
            if self.tipo == "ridge":
                # Nivel y estacionalidad propios de cada planta: poa × planta × (1, doy_sin, doy_cos)
                for p in self.plantas_:
                    base = d["poa"] * dummies[p]
                    X[f"poa_{p}"], X[f"poa_dsin_{p}"], X[f"poa_dcos_{p}"] = base, base * d["doy_sin"], base * d["doy_cos"]
        if self.tipo == "ridge":
            X["poa2"], X["poa_t"] = d["poa"] ** 2, d["poa"] * d["temp_celda"]
        return X

    def _pvwatts(self, d):
        return pvlib.pvsystem.pvwatts_dc(d["poa"], d["temp_celda"], pdc0=1.0, gamma_pdc=GAMMA_PDC).to_numpy()

    def fit(self, d: pd.DataFrame):
        y = d["pvod_power_norm"].to_numpy()
        self.plantas_ = sorted(d["plant_id"].unique())
        if self.tipo == "fisico":
            x = self._pvwatts(d)
            grupos = d["plant_id"] if self.con_planta else pd.Series("todas", index=d.index)
            # k por mínimos cuadrados sin ordenada: k = Σxy / Σx²
            self.k_ = {g: float((x[m] * y[m]).sum() / (x[m] ** 2).sum())
                       for g, m in ((g, (grupos == g).to_numpy()) for g in grupos.unique())}
            return self
        if self.tipo == "ridge":
            self.est_ = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
        elif self.tipo == "rf":
            self.est_ = RandomForestRegressor(n_estimators=150, min_samples_leaf=5, max_features=0.5,
                                              n_jobs=-1, random_state=self.semilla)
        else:
            from xgboost import XGBRegressor  # import tardío: en Mac requiere libomp
            self.est_ = XGBRegressor(n_estimators=500, learning_rate=0.05, max_depth=6, subsample=0.8,
                                     colsample_bytree=0.8, n_jobs=-1, random_state=self.semilla)
        self.columnas_ = list(self._matriz(d).columns)
        self.est_.fit(self._matriz(d)[self.columnas_], y)
        return self

    def predict(self, d: pd.DataFrame) -> np.ndarray:
        if self.tipo == "fisico":
            if self.con_planta:
                k = d["plant_id"].map(self.k_)
                if k.isna().any():
                    raise ValueError(f"Plantas sin entrenar: {sorted(d.loc[k.isna(), 'plant_id'].unique())}")
            else:
                k = self.k_["todas"]
            yhat = self._pvwatts(d) * np.asarray(k)
        else:
            if self.con_planta and not set(d["plant_id"]) <= set(self.plantas_):
                raise ValueError("Plantas sin entrenar; usar un modelo con con_planta=False")
            yhat = self.est_.predict(self._matriz(d)[self.columnas_])
        return np.clip(yhat, 0, None)


def cv_por_mes(d: pd.DataFrame, tipo: str, escenario: str, con_planta: bool = True) -> pd.Series:
    """Predicciones fuera de muestra dejando un mes calendario entero afuera en cada vuelta."""
    oof = pd.Series(np.nan, index=d.index)
    for tr, te in LeaveOneGroupOut().split(d, groups=d["mes_id"]):
        m = ModeloPotencia(tipo, escenario, con_planta).fit(d.iloc[tr])
        oof.iloc[te] = m.predict(d.iloc[te])
    return oof


def energia_diaria(d: pd.DataFrame, yhat) -> pd.DataFrame:
    """Energía por planta y día en MWh/MW (suma de la potencia normalizada horaria)."""
    x = d[["plant_id", "date_local", "pvod_power_norm", "plant_capacity_mw"]].assign(esperado=np.asarray(yhat))
    return (x.groupby(["plant_id", "date_local"])
             .agg(e_real=("pvod_power_norm", "sum"), e_esp=("esperado", "sum"), cap_mw=("plant_capacity_mw", "first"))
             .reset_index())


def metricas(d: pd.DataFrame, yhat) -> dict:
    """MAE/RMSE en fracción de capacidad, R², sesgo de energía y error de energía diaria.

    error_energia_diaria_pct = Σ|E_real,d − E_esp,d| / Σ E_real,d sobre todos los días-planta.
    Es la métrica que se compara con el umbral de la hipótesis.
    """
    y, yhat = d["pvod_power_norm"].to_numpy(), np.asarray(yhat)
    e = energia_diaria(d, yhat)
    return {"MAE": mean_absolute_error(y, yhat), "RMSE": mean_squared_error(y, yhat) ** 0.5,
            "R2": r2_score(y, yhat), "sesgo_energia_pct": 100 * (y.sum() - yhat.sum()) / y.sum(),
            "error_energia_diaria_pct": 100 * (e["e_real"] - e["e_esp"]).abs().sum() / e["e_real"].sum()}
