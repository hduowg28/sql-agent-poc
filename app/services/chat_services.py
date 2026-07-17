from fastapi import HTTPException

from app.agents.sql_agent import agent


class ChatService:

    @staticmethod
    def validate_question(question: str):

        question = question.strip()

        if question == "":
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty."
            )

        if len(question) > 500:
            raise HTTPException(
                status_code=400,
                detail="Question is too long."
            )

        return question

    @staticmethod
    def run_agent(question: str):

        try:

            result = agent.invoke({
                "input": question
            })

            return result

        except Exception as e:

            raise HTTPException(
                status_code=500,
                detail=f"Agent Error: {str(e)}"
            )

    @staticmethod
    def format_response(result):

        answer = result.get("output", "")

        return {
            "success": True,
            "answer": answer
        }

    @classmethod
    def ask(cls, question: str):

        question = cls.validate_question(question)

        result = cls.run_agent(question)

        return cls.format_response(result)