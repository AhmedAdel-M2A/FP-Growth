import openpyxl
import math
from collections import defaultdict
from itertools import combinations


# 1. Read Excel file

def read_transactions():

    ws = openpyxl.load_workbook("Horizontal_Format.xlsx").active

    transactions = []

    for tid, items in ws.iter_rows(min_row=2, values_only=True):

        items = set(x.strip() for x in items.split(","))

        transactions.append((tid, sorted(items)))

    return transactions


# 2. Build FP-Tree

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


# 4. conditional pattern base: every path that ends with this item

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


# 5. FP-Growth: Find Frequent Itemsets

def mine_tree(root, frequent, min_count, frequent_itemsets, suffix=()):

    # least frequent item first
    for item in sorted(frequent, key=lambda x: (frequent[x], x)):

        new_pattern = suffix + (item,)

        frequent_itemsets[tuple(sorted(new_pattern))] = frequent[item]

        paths = []

        find_paths(root, item, [], paths)

        new_root, new_frequent = build_tree(paths, min_count)

        if new_root is not None:
            mine_tree(new_root, new_frequent, min_count, frequent_itemsets, new_pattern)


# 6. Generate Association Rules and Lift


from itertools import combinations

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

# 7. Run Algorithm

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