# Load the newly uploaded dataset
import pandas as pd
import matplotlib.pyplot as plt


file_path = "./data/out.csv"
df = pd.read_csv(file_path)

# Convert sent_time and recv_time into integer bins (seconds)
df["sent_bin"] = df["sent_time"].astype(int)
df["recv_bin"] = df["recv_time"].astype(int)

# Count the number of transactions in each time bin
sent_counts = df.groupby("sent_bin")["id"].count()
recv_counts = df.groupby("recv_bin")["id"].count()

# Define the time range
time_min = int(min(df["sent_time"].min(), df["recv_time"].min()))
time_max = int(max(df["sent_time"].max(), df["recv_time"].max()))
time_index = range(time_min, time_max + 1)

# Ensure both series cover the same time range (fill missing bins with 0)
sent_counts = sent_counts.reindex(time_index, fill_value=0)
recv_counts = recv_counts.reindex(time_index, fill_value=0)

# Compute cumulative sums
sent_cumulative = sent_counts.cumsum()
recv_cumulative = recv_counts.cumsum()

# Calculate in-flight transactions (sent but not yet received)
in_flight = sent_cumulative - recv_cumulative

# Plot cumulative transactions and in-flight transactions
plt.figure(figsize=(10, 6))
plt.plot(
    time_index, sent_counts, label="Cumulative Sent", marker="o", linestyle="-"
)
plt.plot(
    time_index, recv_counts, label="Cumulative Received", marker="o", linestyle="-"
)
plt.plot(
    time_index,
    in_flight,
    label="In Flight (Sent - Received)",
    marker="o",
    linestyle="-",
)

plt.xlabel("Time (seconds)")
plt.ylabel("Number of Transactions")
plt.title("Cumulative Sent vs Received & In-Flight Transactions Over Time")
plt.grid(True)
plt.legend()
plt.savefig("./plots/plot.png")
