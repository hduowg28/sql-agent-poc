from agent import get_sql_agent

def main():
    print("Initializing SQL Agent...")
    agent = get_sql_agent()
    print("Agent is ready! Ask me anything about your database.")
    
    while True:
        query = input("\nText your question (or type 'exit' to quit): ")
        
        if query.strip().lower() == 'exit':
            print("Goodbye!")
            break
            
        if not query.strip(): 
            continue
            
        try:
            print("AI is thinking...")
            response = agent.invoke({"input": query})
            print("\nAnswer:", response["output"])
        except Exception as e:
            print("\nError:", e)

if __name__ == "__main__":
    main()