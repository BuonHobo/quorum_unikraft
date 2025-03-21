# Load the newly uploaded dataset
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def main():
    attempts = 2
    rpses = [1, 20, 40, 60, 80, 100]
    name_to_inputs = {}
    name_to_in_stds = {}
    name_to_outputs = {}
    name_to_out_stds = {}
    name_to_latencies = {}
    name_to_lat_stds = {}
    for consensus in ["raft", "qbft"]:
        for kind in ["baseline", "contract"]:
            name = f"{consensus}_{kind}"
            name_to_inputs[name] = []
            name_to_in_stds[name] = []
            name_to_outputs[name] = []
            name_to_out_stds[name] = []
            name_to_latencies[name] = []
            name_to_lat_stds[name] = []
            for rps in rpses:
                input_throughputs = []
                output_throughputs = []
                latencies = []
                for attempt in range(1, attempts + 1):
                    df = pd.read_csv(f"data/{consensus}_{kind}_{rps}_{attempt}.csv")
                    input_period = df["sent_time"].max() - df["sent_time"].min()
                    output_period = (
                        df["recv_time"].max()
                        - df["recv_time"].where(df["recv_time"] > 0).min()
                    )
                    input_throughput = len(df) / input_period
                    output_throughput = (
                        len(df.where(df["recv_time"] != None)) / output_period
                    )

                    latency = (
                        df["recv_time"].where(df["recv_time"] > 0).mean()
                        - df["sent_time"].mean()
                    )

                    latencies.append(latency)
                    input_throughputs.append(input_throughput)
                    output_throughputs.append(output_throughput)
                name_to_inputs[name].append(np.mean(input_throughputs))
                name_to_in_stds[name].append(np.std(input_throughputs))
                name_to_outputs[name].append(np.mean(output_throughputs))
                name_to_out_stds[name].append(np.std(output_throughputs))
                name_to_latencies[name].append(np.mean(latencies))
                name_to_lat_stds[name].append(np.std(latencies))

    for name in name_to_inputs:
        if "baseline" in name:
            linestyle = "--"
        else:
            linestyle = "-"
        plt.errorbar(
            name_to_inputs[name],
            name_to_outputs[name],
            xerr=name_to_in_stds[name],
            yerr=name_to_out_stds[name],
            linestyle=linestyle,
            label=f"{name}",
        )
    plt.xlim(0, 100)
    plt.ylim(0, 100)
    plt.xlabel("Input Throughput (req/s)")
    plt.ylabel("Output Throughput (req/s)")
    plt.legend()
    plt.savefig("plots/plot2.png")
    plt.clf()
    for name in name_to_latencies:
        if "baseline" in name:
            linestyle = "--"
        else:
            linestyle = "-"
        plt.errorbar(
            name_to_inputs[name],
            name_to_latencies[name],
            yerr=name_to_lat_stds[name],
            xerr=name_to_in_stds[name],
            linestyle=linestyle,
            label=f"{name}",
        )
    plt.xlim(0, 100)
    plt.xlabel("Input Throughput (req/s)")
    plt.ylabel("Response Latency (s)")
    plt.legend()
    plt.savefig("plots/plot3.png")


if __name__ == "__main__":
    main()
