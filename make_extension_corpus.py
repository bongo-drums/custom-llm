"""Write the Experiment B teaching files into corpus/.

Covers three extension-eval categories: opposites, everyday knowledge,
and categories/analogies. This script NEVER reads evals/. All sentences are
hand-written templates with different wording, people, and examples than the
test prompts. A self-check at the end (run separately from the notebook's own
exact-prefix check) makes sure no test sentence or prefix is copied in.

Run:  python make_extension_corpus.py
"""
import itertools
import random
from pathlib import Path

rng = random.Random(7)
OUT = Path("corpus")
# Names deliberately different from every name used in the eval suite.
NAMES = ["priya", "jordan", "kai", "lena", "marco", "tessa", "raj", "zoe", "ben", "iris",
         "hugo", "mia", "tom", "rosa", "dev", "lucy"]
PLACES = ["at home", "at school", "in the park", "at the store", "in the kitchen", "in the office"]


def pick(seq):
    return rng.choice(seq)


# ---------------------------------------------------------------- opposites
# Pattern pairs taught with the "opposite of" frame. The three test pairs
# (hot/cold, empty/full, noisy/quiet) are NOT given this frame.
PATTERN_PAIRS = [("big", "small"), ("tall", "short"), ("happy", "sad"), ("fast", "slow"),
                 ("up", "down"), ("hard", "soft"), ("early", "late"), ("heavy", "light"),
                 ("open", "shut"), ("old", "young"), ("wet", "dry"), ("clean", "dirty"),
                 ("rich", "poor"), ("strong", "weak"), ("near", "far"), ("thick", "thin"),
                 ("long", "short"), ("bright", "dim"), ("warm", "cool"), ("loud", "soft"),
                 ("day", "night"), ("win", "lose")]
# Test-relevant words, taught only through contrast in everyday scenes.
CONTRAST_SCENES = {
    ("hot", "cold"): [
        "the soup is hot but the juice is cold .", "in summer the sand feels hot and in winter the snow feels cold .",
        "{n} likes hot tea in the morning and cold water after a run .", "the oven is hot . the fridge is cold .",
        "{n} touched the hot pan and then held a cold glass .", "hot and cold are opposites .",
        "cold is the word for the other end from hot .", "the tap gives hot water on the left and cold water on the right .",
        "a desert day is hot while a mountain night is cold .", "{n} said the room was too hot , so she opened a window to let in cold air ."],
    ("empty", "full"): [
        "the jar was empty in the morning and full by night .", "{n} filled the empty bottle until it was full .",
        "the bus is full at noon but empty at midnight .", "empty and full are opposites .",
        "full is the word for the other end from empty .", "after lunch the plate was empty and {n} was full .",
        "{n} carried a full box in and an empty box out .", "the tank was full on monday and empty on friday .",
        "a full cup has no room left , an empty cup has lots of room .", "the store shelf looked empty until the truck made it full again ."],
    ("noisy", "quiet"): [
        "the street is noisy but the library is quiet .", "{n} left the noisy party for a quiet walk .",
        "noisy and quiet are opposites .", "quiet is the word for the other end from noisy .",
        "the classroom was noisy at recess and quiet during the test .", "a noisy dog barks , a quiet cat sleeps .",
        "the city is noisy at rush hour and quiet at dawn .", "{n} asked the noisy team to be quiet .",
        "the kitchen was noisy while cooking and quiet after dinner .", "a quiet room helps {n} read , a noisy room does not ."],
}


def opposites():
    lines = set()
    for a, b in PATTERN_PAIRS:
        lines.add(f"the opposite of {a} is {b} .")
        lines.add(f"the opposite of {b} is {a} .")
        lines.add(f"{a} and {b} are opposites .")
        for n in rng.sample(NAMES, 4):
            lines.add(f"{n} learned that the opposite of {a} is {b} .")
            lines.add(f"{n} asked what the opposite of {b} is . the answer is {a} .")
        lines.add(f"if something is not {a} , it may be {b} .")
    for scenes in CONTRAST_SCENES.values():
        for s in scenes:
            if "{n}" in s:
                for n in rng.sample(NAMES, 5):
                    lines.add(s.format(n=n))
            else:
                lines.add(s)
    return sorted(lines)


# -------------------------------------------------------- everyday knowledge
def everyday():
    lines = set()
    ice = ["when it gets very cold , water turns into ice .", "the pond freezes in winter and becomes solid ice .",
           "{n} put water in the freezer and later found ice .", "ice is frozen water .",
           "ice melts back into water in the sun .", "when water boils it turns into steam .",
           "steam rises from the hot kettle .", "cold water becomes ice , hot water becomes steam .",
           "{n} added ice to keep the juice cold .", "the lake was covered in ice after the cold night ."]
    umbrella = ["{n} carries an umbrella when it rains so she stays dry .", "without an umbrella , {n} got wet in the rain .",
                "an umbrella keeps your head dry in a storm .", "{n} opened an umbrella and stayed dry on the walk .",
                "rain makes clothes wet , but an umbrella keeps them dry .", "{n} forgot the umbrella and came home wet .",
                "people hold an umbrella over their heads to keep dry .", "a raincoat and an umbrella help you stay dry ."]
    light = ["when the room is dark , {n} turns on the light .", "at night we switch on a light so we can see .",
             "{n} could not see in the dark hallway until she turned on the light .", "a lamp gives light in a dark room .",
             "it was dark , so {n} turned on the light to find her keys .", "light helps us see when it is dark .",
             "turn off the light to sleep and turn on the light to read .", "the dark kitchen was bright again once the light came on ."]
    other = ["{n} slept with her head on a soft pillow .", "we eat soup with a spoon .", "{n} tied the lace on her shoe .",
             "a table can be made of wood .", "children build castles from sand at the beach .",
             "{n} was hungry , so she ate lunch .", "the baby fell asleep after a long day .",
             "a person uses a spoon to eat and a pillow to sleep .", "{n} uses a towel to get dry after a swim .",
             "we use a key to open a door .", "{n} uses a map to find the way .", "a person wears a shoe on each foot ."]
    for group in (ice, umbrella, light, other):
        for s in group:
            if "{n}" in s:
                for n in rng.sample(NAMES, 6):
                    lines.add(s.format(n=n))
            else:
                lines.add(s)
    return sorted(lines)


# --------------------------------------------------- categories & analogies
MEMBERS = {
    "bird": ["sparrow", "eagle", "owl", "crow", "parrot", "robin"],
    "fish": ["trout", "tuna", "shark", "cod", "salmon"],
    "tree": ["oak", "pine", "maple", "willow"],
    "tool": ["hammer", "saw", "wrench", "drill"],
    "vegetable": ["potato", "onion", "pea", "broccoli", "carrot"],
    "fruit": ["banana", "pear", "grape", "mango", "peach", "apple"],
    "fabric": ["cotton", "wool", "silk", "denim"],
    "metal": ["iron", "copper", "steel", "gold"],
    "vehicle": ["car", "bus", "truck", "bicycle", "taxi"],
    "animal": ["dog", "cat", "horse", "goat", "duck"],
}
YOUNG = [("calf", "cow"), ("lamb", "sheep"), ("chick", "hen"), ("foal", "horse"), ("cub", "bear"),
         ("duckling", "duck"), ("kid", "goat"), ("tadpole", "frog"), ("caterpillar", "butterfly"),
         ("seed", "plant"), ("puppy", "dog"), ("kitten", "cat")]
# Test-case sentences we must never reproduce, even outside their full prompt.
AVOID = {("robin", "bird"), ("salmon", "fish"), ("carrot", "vegetable"), ("apple", "fruit")}
AVOID_GROW = {("puppy", "dog"), ("kitten", "cat")}


def article(word):
    return "an" if word[0] in "aeiou" else "a"


def categories():
    lines = set()
    for cat, members in MEMBERS.items():
        for m in members:
            if (m, cat) in AVOID:
                # Teach the fact only in a different frame from the test.
                lines.add(f"the {m} belongs with the other kinds of {cat} .")
                lines.add(f"{pick(NAMES)} read that the {m} is one kind of {cat} .")
                continue
            lines.add(f"{article(m)} {m} is {article(cat)} {cat} .")
            others = [x for x in members if x != m and (x, cat) not in AVOID]
            if others:
                o = pick(others)
                lines.add(f"{article(o)} {o} is {article(cat)} {cat} . {article(m)} {m} is {article(cat)} {cat} .")
        # Cross-category pairs teach the "X is a A . Y is a B" analogy frame.
    cats = list(MEMBERS)
    for c1, c2 in itertools.permutations(cats, 2):
        m1 = pick([m for m in MEMBERS[c1] if (m, c1) not in AVOID])
        m2 = pick([m for m in MEMBERS[c2] if (m, c2) not in AVOID])
        lines.add(f"{article(m1)} {m1} is {article(c1)} {c1} . {article(m2)} {m2} is {article(c2)} {c2} .")
    for young, adult in YOUNG:
        if (young, adult) in AVOID_GROW:
            lines.add(f"a young {adult} is called {article(young)} {young} .")
            lines.add(f"{pick(NAMES)} watched the little {young} become a big {adult} .")
            continue
        lines.add(f"{article(young)} {young} grows into {article(adult)} {adult} .")
    safe = [(y, a) for y, a in YOUNG if (y, a) not in AVOID_GROW]
    for (y1, a1), (y2, a2) in itertools.permutations(safe, 2):
        lines.add(f"{article(y1)} {y1} grows into {article(a1)} {a1} . {article(y2)} {y2} grows into {article(a2)} {a2} .")
    return sorted(lines)


def main():
    OUT.mkdir(exist_ok=True)
    files = {"opposites.txt": opposites(), "everyday_knowledge.txt": everyday(),
             "categories_and_analogies.txt": categories()}
    for name, lines in files.items():
        (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{name}: {len(lines)} unique passages")


if __name__ == "__main__":
    main()
