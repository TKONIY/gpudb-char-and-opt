#!/usr/bin/env python3

import os
import time
import argparse
import subprocess as subp

from threading import Thread
from utility.profiler_logger import LOGGER


def launch_cmd(cmd):
    out, _ = subp.Popen(
        cmd.split(" "),
        stdin=subp.PIPE,
        stdout=subp.PIPE,
        stderr=subp.STDOUT,
    ).communicate()
    return out.decode("utf-8")


def get_device():
    device_list = launch_cmd("nvidia-smi -L").strip("\n").split("\n")
    for i, device in enumerate(device_list):
        device = device.strip(")")
        device = device.split(":")[-1].strip(" ")
        device_list[i] = device
    return device_list


def start_server(num_iter):
    py_interpreter = "./blazingsql/.local/miniconda3/envs/bsql/bin/python3"
    subp.Popen(
        [
            py_interpreter,
            "./scheduler/blazingsql_execute_query.py",
            "--num-iter={}".format(num_iter),
        ],
        env=os.environ.copy(),
    ).wait()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--iter",
        type=int,
        required=True,
        help="Number of iterations to run SSB benchmarks.",
    )
    parser.add_argument(
        "--sf",
        type=int,
        default=2,
        help="Scale factor to run SSB benchmarks.",
    )
    args = parser.parse_args()

    with open("./.log/profiler.log", "w") as f:
        f.close()

    mig_list = [d for d in get_device() if "MIG" in d]

    total_t = time.perf_counter() * 1000

    thread_pool = []
    for i in range(len(mig_list)):
        os.environ["CUDA_VISIBLE_DEVICES"] = mig_list[i]
        thread_pool.append(Thread(target=start_server, args=(args.iter,)))
    for t in thread_pool:
        t.join()

    total_t = time.perf_counter() * 1000 - total_t
    print(f"Total: {total_t:.3f} ms")


if __name__ == "__main__":
    main()
