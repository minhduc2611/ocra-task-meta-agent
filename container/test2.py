# import json
# from libs.google_vertex import add_citations
# from vertexai.preview.generative_models import GenerationResponse

# with open("response.json", "r", encoding="utf-8") as f:
#     response = json.load(f)

# res = GenerationResponse.from_dict(response)
# text = add_citations(res)
# print("*"*100)
# print(res.text)
# print("*"*100)
# print(text)
# print("*"*100)


# from agents.tools.buddha_agent_builder_tools import generate_buddhist_system_prompt
from libs.open_ai import basic_openai_answer
def get_result():
    # result = await generate_buddhist_system_prompt(focus="Buddhist Search & Review", language="vi")
    # print("***")
    # print(result)
    # print("***")
    result = basic_openai_answer(query=f"Generate a system prompt for a Buddhist agent based on focus area and language. Focus: Buddhist Search & Review, Language: vi")
    print("***")
    print(result)
    print("***")

get_result()
print("end")