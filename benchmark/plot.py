# Load the newly uploaded dataset
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def main():
    name_to_data = {}

    for file in os.listdir("data"):
        if not file.endswith(".csv"):
            continue
        name, rps, attempt = file.removesuffix(".csv").split("_")
        rps = int(rps)
        attempt = int(attempt)
        name = name
        if name not in name_to_data:
            name_to_data[name] = {}
            for datapoint in ["input", "output", "latency"]:
                name_to_data[name][datapoint] = {
                    "std": [],
                    "mean": [],
                    "datapoints": {},
                }
        for datapoint in ["input", "output", "latency"]:
            if rps not in name_to_data[name][datapoint]["datapoints"]:
                name_to_data[name][datapoint]["datapoints"][rps] = []
        df = pd.read_csv(f"data/{file}")
        input_period = df["sent_time"].max() - df["sent_time"].min()
        output_period = (
            df["recv_time"].max() - df["recv_time"].where(df["recv_time"] > 0).min()
        )
        input_throughput = len(df) / input_period
        output_throughput = len(df.where(df["recv_time"] != None)) / output_period

        latency = (
            df["recv_time"].where(df["recv_time"] > 0).mean() - df["sent_time"].mean()
        )

        name_to_data[name]["input"]["datapoints"][rps].append(input_throughput)
        name_to_data[name]["output"]["datapoints"][rps].append(output_throughput)
        name_to_data[name]["latency"]["datapoints"][rps].append(latency)

    for data in name_to_data.values():
        for datapoint in ["input", "output", "latency"]:
            for attemps in data[datapoint]["datapoints"].values():
                data[datapoint]["mean"].append(np.mean(attemps))
                data[datapoint]["std"].append(np.std(attemps))

    for name, data in name_to_data.items():
        if "baseline" in name:
            linestyle = "--"
        else:
            linestyle = "-"
        plt.errorbar(
            data["input"]["mean"],
            data["output"]["mean"],
            xerr=data["input"]["std"],
            yerr=data["output"]["std"],
            linestyle=linestyle,
            label=f"{name}",
        )
    plt.xlabel("Input Throughput (req/s)")
    plt.ylabel("Output Throughput (req/s)")
    plt.legend()
    plt.savefig("plots/throughput.png")
    plt.clf()

    for name, data in name_to_data.items():
        if "baseline" in name:
            linestyle = "--"
        else:
            linestyle = "-"
        plt.errorbar(
            data["input"]["mean"],
            data["latency"]["mean"],
            yerr=data["latency"]["std"],
            xerr=data["input"]["std"],
            linestyle=linestyle,
            label=f"{name}",
        )
    plt.xlabel("Input Throughput (req/s)")
    plt.ylabel("Response Latency (s)")
    plt.legend()
    plt.savefig("plots/latency.png")


if __name__ == "__main__":
    main()
