from services.rag_service import process_query


def main():
    print("[RAG] System Ready! Type 'exit' to quit.\n")

    # 🔐 Ask role dynamically (important for testing RBAC)
    user_role = input("Enter your role (finance/hr/marketing/admin): ").strip().lower()

    print(f"[AUTH] Logged in as role: '{user_role}'")

    while True:
        query = input("\nUser: ").strip()

        if query.lower() in ["exit", "quit"]:
            print("Exiting RAG system...")
            break

        # 🚫 Handle empty input
        if not query:
            print("⚠️ Please enter a valid question.")
            continue

        try:
            response = process_query(query, user_role)
            print(f"Assistant: {response}")

        except Exception as e:
            print("❌ Error:", str(e))


if __name__ == "__main__":
    main()