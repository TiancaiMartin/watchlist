import openai

api_key = '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'

def generate_movie_box_office_analysis(movie_name):
    prompt_text = f"生成关于电影《{movie_name}》的票房分析，并列出具体的票房数据。（200字以内）"

    client = openai.OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt_text,
            }
        ],
        model="gpt-3.5-turbo",
    )

    return response.choices[0].message.content.strip()

#input_movie = input("输入电影名：")
#print(generate_movie_box_office_analysis(input_movie))