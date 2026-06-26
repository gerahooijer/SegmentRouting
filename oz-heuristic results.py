from itertools import product
import pandas as pd
import os
from glob import glob
from collections import defaultdict

from pandas import to_numeric

results = []
best_result = defaultdict()

for k in range(1,13):
    solved = set()

    input_folder = f"results-oz\\seperate"
    csv_files = glob(os.path.join(input_folder, "*.csv"))

    for file in csv_files:
        instance = 0
        for bp in [True, False]:
            for pc in [True, False]:
                for heur in [True, False]:
                    for i in range(1, 13):
                        if f"results-oz\\seperate\\multi_results_instance_OZ{i}({bp}, {pc}, {heur}).csv" in file:
                            instance = i
                            bp1 = bp
                            pc1 = pc
                            heur1 = heur
        if instance != k: continue

        algorithm_name = "CBS"
        if bp1 == True:
            algorithm_name += "-BP"
        if pc1 == True:
            algorithm_name += "-PC"
        if heur1 == True:
            algorithm_name += "-HEUR"

        df = pd.read_csv(file)

        for index in range(50):

            if (algorithm_name, instance, index) in best_result:
                if best_result[(algorithm_name, instance, index)] > pd.to_numeric(df["score"][index]):
                    best_result[(algorithm_name, instance, index)] = pd.to_numeric(df["score"][index])
            elif df["score"][index] != "infeasible" and (algorithm_name, instance, index) not in best_result:
                best_result[(algorithm_name, instance, index)] = pd.to_numeric(df["score"][index])

            if df["score"][index] != "infeasible" and heur1 == False:
                solved.add(index)
    print(best_result)
    print("number of not instances solved:", len(solved))

    for file in csv_files:
        instance = 0
        for bp in [True, False]:
            for pc in [True, False]:
                for heur in [True, False]:
                    for i in range(1, 13):
                        if f"results-oz\\seperate\\multi_results_instance_OZ{i}({bp}, {pc}, {heur}).csv" in file:
                            instance = i
                            bp1 = bp
                            pc1 = pc
                            heur1 = heur
        if instance != k: continue

        df = pd.read_csv(file)

        for index in range(50):

            if df["score"][index] == "infeasible" and heur1 == True:
                if index in solved:
                    solved.remove(index)

    avg_score = 0
    avg_scores = {}
    calculated = set()
    avg_scores["optimal"] = 0
    avg_scores["CBS-BP-HEUR"] = 0
    avg_scores["CBS-PC-HEUR"] = 0
    avg_scores["CBS-HEUR"] = 0
    avg_scores["CBS-BP-PC-HEUR"] = 0

    for file in csv_files:
        df = pd.read_csv(file)
        optimal_score = {}

        instance = 0
        for bp in [True, False]:
            for pc in [True, False]:
                for heur in [True, False]:
                    for i in range(1, 13):
                        if f"results-oz\\seperate\\multi_results_instance_OZ{i}({bp}, {pc}, {heur}).csv" in file:
                            instance = i
                            bp1 = bp
                            pc1 = pc
                            heur1 = heur
        if instance != k: continue

        algorithm_name = "CBS"
        if bp1 == True:
            algorithm_name += "-BP"
        if pc1 == True:
            algorithm_name += "-PC"
        if heur1 == True:
            algorithm_name += "-HEUR"
        feasible = df["score"] != "infeasible"

        score = 0
        instances_solved = len(solved)

        for index in range(50):
            if index in solved:
                if heur1 == False and index not in calculated:
                    if df["score"][index] != "infeasible":
                        calculated.add(index)
                        optimal_score[index] = df["score"][index]
                        avg_score += pd.to_numeric(df["score"][index]) / instances_solved if instances_solved > 0 else 0
                        avg_scores["optimal"] += pd.to_numeric(df["score"][index]) / instances_solved if instances_solved > 0 else 0

                elif heur1 ==True:
                    avg_scores[algorithm_name] += pd.to_numeric(df["score"][index]) / instances_solved if instances_solved > 0 else 0

    results.append({
        "instance": k,
        "instances-solved": instances_solved,
        "optimal": avg_scores["optimal"],
        "CBS-H": avg_scores["CBS-HEUR"],
        "ratioCBS": avg_scores["CBS-HEUR"] / avg_scores["optimal"]*100 if avg_scores["optimal"] != 0 else None,
        "CBS-PC-H": avg_scores["CBS-PC-HEUR"],
        "ratioCBS-PC": avg_scores["CBS-PC-HEUR"] / avg_scores["optimal"]*100 if avg_scores["optimal"] != 0 else None,
        "CBS-BP-H": avg_scores["CBS-BP-HEUR"],
        "ratioCBS-BP": avg_scores["CBS-BP-HEUR"] / avg_scores["optimal"]*100 if avg_scores["optimal"] != 0 else None,
        "CBS-BP-PC-H": avg_scores["CBS-BP-PC-HEUR"],
        "ratioCBS-BP-PC": avg_scores["CBS-BP-PC-HEUR"] / avg_scores["optimal"]*100 if avg_scores["optimal"] != 0 else None,

    })
    print(avg_score)

new_df = pd.DataFrame(results)
new_df.to_csv(f"heuristic-results-oz.csv", index=False)
