FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0"]

%%writefile complaintpro/requirements.txt
fastapi
uvicorn
streamlit
kafka-python
websockets
transformers
torch
scikit-learn
pandas
numpy
matplotlib
seaborn
plotly
wordcloud
dvc[s3]
mlflow
