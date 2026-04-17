# app.py

from services.rag_service import process_query


def main():
    print("🔐 Secure Enterprise RAG System")
    print("Type 'exit' to quit.\n")

    # 🔐 Role input
    user_role = input("Enter your role (finance/hr/marketing/engineering/admin): ").strip().lower()

    if not user_role:
        print("❌ Role is required. Exiting.")
        return

    print(f"[AUTH] Logged in as role: '{user_role}'")

    while True:
        query = input("\nUser: ").strip()

        # Exit condition
        if query.lower() in ["exit", "quit"]:
            print("Exiting RAG system...")
            break

        # Empty input check
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