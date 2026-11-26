import openpyxl
import math
from collections import defaultdict
from itertools import combinations
from openpyxl.chartsheet import relation


# 1. Read Excel file

def read_transactions():

    ws = openpyxl.load_workbook("Horizontal_Format.xlsx").active

    transactions = []

    for tid, items in ws.iter_rows(min_row=2, values_only=True):

        items = set(x.strip() for x in items.split(","))

        transactions.append((tid, sorted(items)))

    return transactions



def build_tree(transactions, min_count):

    # count the support of every item
    count = defaultdict(int)

    for items in transactions:
        for item in items:
            count[item] += 1

    # keep only frequent items
    frequent = {}

    for item in count:
        if count[item] >= min_count:
            frequent[item] = count[item]

    # no frequent items -> no tree
    if not frequent:
        return None, {}

    # order: higher support first, alphabetical if equal
    sorted_items = sorted(frequent, key=lambda x: (-frequent[x], x))

    order = {}

    i = 0
    for item in sorted_items:
        order[item] = i
        i += 1

    root = {"item": None, "count": 0, "children": {}}

    # second pass: insert every transaction into the tree
    for items in transactions:

        # remove infrequent items, then sort by the order above
        items = [x for x in items if x in frequent]
        items.sort(key=lambda x: order[x])

        current = root

        for item in items:

            # create the node if it is not already a child
            if item not in current["children"]:
                current["children"][item] = {
                    "item": item,
                    "count": 0,
                    "children": {}
                }

            current = current["children"][item]
            current["count"] += 1

    return root, frequent


# 3. Print FP-Tree

def print_tree(node, level=0):

    if level == 0:
        print("Root")

    for item, child in node["children"].items():

        print("   " * (level + 1) + f"|-- {item}:{child['count']}")

        print_tree(child, level + 1)


# conditional pattern base: every path that ends with this item

def find_paths(node, item, path, paths):

    for child_item, child in node["children"].items():

        if child_item == item:

            # an item appears only once on a path, so stop here
            if path:
                # the path appears "count" times, so add it "count" times
                for _ in range(child["count"]):
                    paths.append(list(path))

        else:
            find_paths(child, item, path + [child_item], paths)


# 4. FP-Growth: Find Frequent Itemsets

def mine_tree(root, frequent,min_support_count, frequent_itemsets, suffix=()):

    # only get the keys (letters) form the frequent dict
    items = list(frequent.keys())

    items.sort(key = lambda item: (frequent[item], item))

    for item in items :
        new_pattern = suffix + (item,)

        # make the pattern in a key form then save the pattern in the freq_itemset
        pattern_itemsets= tuple(sorted(new_pattern))
        frequent_itemsets[pattern_itemsets] = frequent[item]

        # search for all paths ends with (item) and save them in (paths)
        paths = []
        find_paths(root , item , [], paths)

        #build new conditional tree and recurs again until the root is null
        new_root, new_frequent = build_tree(paths, min_support_count)

        if new_root is not None and new_frequent:
            mine_tree(new_root,new_frequent, min_support_count,frequent_itemsets, new_pattern)


# 5. Generate Association Rules and Lift



def generate_rules(frequent_itemsets):

    rules = []

    for itemset in frequent_itemsets:
        lenitemset = len(itemset)

        if lenitemset < 2:
            continue

        for i in range(1, lenitemset):
            for antecedent in combinations(itemset, i):

                antecedentSet = set(antecedent)

                consequent = tuple(
                    item for item in itemset
                    if item not in antecedentSet
                )

                rules.append({
                    "antecedent": antecedent,
                    "consequent": consequent
                })

    return rules


# 6 & 7 extract string rules and lift
def extract_strong_rules(rules,frequent_itemsets,total_transactions,min_confidence,min_support):

    strong_rules = []

    for rule in rules:
        ant = rule["antecedent"]
        cons = rule["consequent"]

        ant_list = list(ant)
        ant_list.sort()
        ant_itemset = tuple(ant_list)

        cons_list = list(cons)
        cons_list.sort()
        cons_itemset = tuple(cons_list)

        union_list = ant_list + cons_list
        union_list.sort()
        union_key = tuple(union_list)

        if (ant_itemset not in frequent_itemsets
            or cons_itemset not in frequent_itemsets
            or union_key not in frequent_itemsets
        ):
            continue

        ant_count = frequent_itemsets[ant_itemset]
        cons_count = frequent_itemsets[cons_itemset]
        union_count = frequent_itemsets[union_key]



        #compute support and confidence for X -> Y
        support = union_count / total_transactions
        confidence = union_count / ant_count


        if support >= min_support and confidence >= min_confidence:


            ant_support = ant_count / total_transactions
            cons_support = cons_count / total_transactions

           
            lift = support / (ant_support * cons_support)

            if   lift == 1:
                relation = "independent"

            elif lift > 1:
                relation = "dependent, + correlated"
            else:
                relation = "dependent, - correlated"

            strong_rules.append({
                "antecedent": ant,
                "consequent": cons,
                "support": support,
                "confidence": confidence,
                "lift": lift,
                "relation": relation,
            })

    return strong_rules





# 8. Run Algorithm

transactions = read_transactions()

total = len(transactions)

# Different minimum support values

support_values = [0.6, 0.8]

confidence_values = [0.7, 0.8]


# items only (the tid is not needed)

transaction_items = [items for tid, items in transactions]


for min_support in support_values:

    min_count = math.ceil(min_support * total)

    print("\n===================================")
    print("Minimum Support:", min_support)
    print("Minimum Count:", min_count)
    print("===================================")

    root, frequent = build_tree(transaction_items, min_count)

    if root is None:
        print("No frequent items")
        continue


    # Print FP-Tree

    print("\nFP-Tree:")

    print_tree(root)

    # Find Frequent Itemsets

    frequent_itemsets = {}

    mine_tree(root, frequent, min_count, frequent_itemsets)

    print("\nFrequent Itemsets:")

    for level in range(1, max(map(len, frequent_itemsets), default=0) + 1):

        print("\nL" + str(level))

        for itemset, count in sorted(frequent_itemsets.items()):

            if len(itemset) == level:

                print(
                    itemset,
                    "Count:", count,
                )

    # Generate Association Rules (only strong ones are printed)

    for min_confidence in confidence_values:

        _, strong_rules = generate_rules(frequent_itemsets, total, min_confidence)

        print("\nStrong Rules (Minimum Confidence:", min_confidence, ")")

        for rule in strong_rules:
            print(rule)


print("\nProgram Finished!")