from sentence_transformers import SentenceTransformer, CrossEncoder

model1 = SentenceTransformer('multi-qa-mpnet-base-dot-v1')
model2 = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
