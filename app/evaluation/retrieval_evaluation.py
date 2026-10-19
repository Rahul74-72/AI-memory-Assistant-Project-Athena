from app.memory.memory_store import MemoryStore
import argparse


def print_results(
    title,
    results
):

    print()
    print("=" * 60)
    print(title)
    print("=" * 60)

    if not results:

        print("No results found.")

        return

    for index, result in enumerate(
        results,
        start=1
    ):

        memory = result["memory"]

        print()
        print(f"Rank: {index}")

        print(
            f"Memory: "
            f"{memory.subject} "
            f"{memory.relation} "
            f"{memory.value}"
        )

        print(
            f"Semantic Score: "
            f"{result['semantic_score']:.4f}"
        )

        print(
            f"Relation Bonus: "
            f"{result['relation_bonus']:.4f}"
        )

        print(
            f"Importance Bonus: "
            f"{result['importance_bonus']:.4f}"
        )

        print(
            f"Recency Bonus: "
            f"{result['recency_bonus']:.4f}"
        )

        print(
            f"Conflict Penalty: "
            f"{result['conflict_penalty']:.4f}"
        )

        print(
            f"Final Score: "
            f"{result['score']:.4f}"
        )


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, required=True)
    args = parser.parse_args()
    store = MemoryStore(args.user_id)

    try:

        # -----------------------------------------
        # Location retrieval
        # -----------------------------------------

        results = store.semantic_search(
            "Where do I live?",
            top_k=5,
            threshold=0.20
        )

        print_results(
            "LOCATION RETRIEVAL",
            results
        )

        # -----------------------------------------
        # Likes retrieval
        # -----------------------------------------

        results = store.semantic_search(
            "What do I like?",
            top_k=5,
            threshold=0.20
        )

        print_results(
            "LIKES RETRIEVAL",
            results
        )

        # -----------------------------------------
        # Study retrieval
        # -----------------------------------------

        results = store.semantic_search(
            "What do I study?",
            top_k=5,
            threshold=0.20
        )

        print_results(
            "STUDY RETRIEVAL",
            results
        )

        # -----------------------------------------
        # Goal retrieval
        # -----------------------------------------

        results = store.semantic_search(
            "What is my goal?",
            top_k=5,
            threshold=0.20
        )

        print_results(
            "GOAL RETRIEVAL",
            results
        )

    finally:

        store.close()


if __name__ == "__main__":

    main()
