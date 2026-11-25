import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression


def calculate_health(metrics):
    cpu = metrics["cpu_percent"]
    memory = metrics["memory_percent"]
    disk = metrics["disk_percent"]
    if cpu >= 90 or memory >= 90 or disk >= 95:
        return "Critical"
    if cpu >= 75 or memory >= 75 or disk >= 85:
        return "Warning"
    return "Healthy"


def analyze_history(records):
    if not records:
        return {"risk": "Low", "anomalies": [], "predictions": {}, "recommendations": []}

    dataframe = pd.DataFrame(records)
    for column in ["cpu_percent", "memory_percent", "disk_percent"]:
        if column in dataframe:
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    predictions = {}
    anomalies = []

    for resource, column in [("CPU", "cpu_percent"), ("Memory", "memory_percent"), ("Disk", "disk_percent")]:
        series = dataframe[column].dropna()
        if len(series) >= 3:
            x = pd.DataFrame({"time_index": range(len(series))})
            model = LinearRegression().fit(x, series)
            predicted = float(model.predict(pd.DataFrame({"time_index": [len(series) + 5]}))[0])
            predicted = round(max(0, min(100, predicted)), 1)
            slope = float(model.coef_[0])
            trend = "Increasing" if slope > 0.25 else "Decreasing" if slope < -0.25 else "Stable"
            predictions[resource] = {"value": predicted, "trend": trend}

            current = float(series.iloc[-1])
            if (predicted >= 85 or current >= 90):
                anomalies.append({"resource": resource, "value": current, "predicted": predicted,
                                  "message": f"{resource} usage or near-term prediction is unusually high."})

    if len(dataframe) >= 10:
        features = dataframe[["cpu_percent", "memory_percent", "disk_percent"]].dropna()
        if len(features) >= 10:
            forest = IsolationForest(contamination=0.12, random_state=42)
            labels = forest.fit_predict(features)
            latest_label = int(labels[-1])
            if latest_label == -1:
                anomalies.append({"resource": "System", "value": 0, "predicted": 0,
                                  "message": "The Isolation Forest model detected an abnormal system state."})

    latest = records[-1]
    cpu = latest["cpu_percent"]
    memory = latest["memory_percent"]
    disk = latest["disk_percent"]

    if len(anomalies) >= 2 or cpu >= 90 or memory >= 90:
        risk = "High"
    elif anomalies or cpu >= 75 or memory >= 75 or disk >= 85:
        risk = "Medium"
    else:
        risk = "Low"

    recommendations = []
    if cpu >= 75:
        recommendations.append("Review the top CPU-consuming processes and allow active tasks or updates to finish. No process was terminated.")
    if memory >= 75:
        recommendations.append("Close applications you recognize and no longer need. Save work before closing any application.")
    if disk >= 85:
        recommendations.append("Review large or temporary files and move or delete only personal data you no longer need. Do not delete system files.")
    if predictions:
        for resource, prediction in predictions.items():
            if prediction["value"] >= 85:
                recommendations.append(f"{resource} may reach {prediction['value']}% soon. Prepare for possible bottlenecks.")
    if not recommendations:
        recommendations.append("No immediate resource action is required. Continue monitoring system performance.")

    return {"risk": risk, "anomalies": anomalies, "predictions": predictions,
            "recommendations": recommendations}


def run_controlled_verification(metrics, before_metrics):
    if before_metrics is None:
        return "Not enough metric history to compare before and after a recommendation."
    cpu_change = round(metrics["cpu_percent"] - before_metrics["cpu_percent"], 1)
    memory_change = round(metrics["memory_percent"] - before_metrics["memory_percent"], 1)
    return f"Verification: CPU changed by {cpu_change:+.1f}% and memory by {memory_change:+.1f}% since review. No process was changed automatically."
