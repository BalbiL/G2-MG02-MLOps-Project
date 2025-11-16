# %%time

# print("Creating Mixed Negative Sampling dataset for Retrieval...")

# mns_training_data_rows = []
# NUM_RANDOM_NEGATIVES = 2

# for _, row in all_behaviors_df.iterrows():
#     history = str(row['history']).split()
#     if not history: # Skip sessions with no history
#         continue
        
#     clicked_news, non_clicked_news = parse_impressions(row['impressions'])
    
#     # Set of items in this impression to avoid sampling them as "random"
#     impression_set = set(clicked_news) | set(non_clicked_news)
    
#     for positive_news in clicked_news:
#         # 1. Add the positive sample
#         mns_training_data_rows.append({
#             "history": history,
#             "candidate_news_id": positive_news,
#             "label": 1
#         })
        
#         # 2. Add one hard negative (if available)
#         if non_clicked_news:
#             hard_negative = np.random.choice(non_clicked_news)
#             mns_training_data_rows.append({
#                 "history": history,
#                 "candidate_news_id": hard_negative,
#                 "label": 0
#             })
            
#         # 3. Add random negatives
#         for _ in range(NUM_RANDOM_NEGATIVES):
#             random_negative = np.random.choice(all_news_ids_list)
#             # Ensure it's not in history or this impression
#             while (random_negative in impression_set or random_negative in history):
#                 random_negative = np.random.choice(all_news_ids_list)
                
#             mns_training_data_rows.append({
#                 "history": history,
#                 "candidate_news_id": random_negative,
#                 "label": 0
#             })

# mns_training_df = pd.DataFrame(mns_training_data_rows)