mkdir -p temp
mkdir -p models
cd temp
wget https://github.com/api-ai/api-ai-english-asr-model/releases/download/1.0/api.ai-kaldi-asr-model.zip
wget https://kaldi-asr.org/models/3/0003_sre16_v2_1a.tar.gz 
tar -xzf 0001_aspire_chain_model.tar.gz -C ../models/
tar -xzf 0003_sre16_v2_1a.tar.gz -C ../models/
rm -rf temp
cd ..
 