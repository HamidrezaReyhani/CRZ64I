import random
from lark import Lark
from lark.exceptions import LarkError


def fuzz_parser(grammar_file, iterations=1000, timeout=0.1):
    """Fuzz the parser with random inputs."""
    with open(grammar_file, 'r') as f:
        grammar = f.read()
    parser = Lark(grammar, start="program", parser="earley", lexer="dynamic", propagate_positions=True, cache=False)
    crashes = 0
    for i in range(iterations):
        # Generate random string
        length = random.randint(1, 100)
        txt = ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \n\t{}();[],.') for _ in range(length))
        try:
            parser.parse(txt)
        except LarkError:
            pass  # Expected
        except Exception as e:
            print(f"Crash on iteration {i}: {e}")
            crashes += 1
            if crashes > 10:  # Stop after too many crashes
                break
    if crashes == 0:
        print("No crashes found.")
    else:
        print(f"Found {crashes} crashes.")


if __name__ == "__main__":
    fuzz_parser("src/crz/compiler/crz64i.lark")
