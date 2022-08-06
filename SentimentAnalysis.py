from transformers import pipeline
def isOffensive(st):
    seq = pipeline(task="text-classification", model = "nlptown/bert-base-multilingual-uncased-sentiment")
    return  seq(st)