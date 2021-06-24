mkdir -p temp
mkdir -p models
cd temp
wget https://kaldi-asr.org/models/1/0001_aspire_chain_model.tar.gz
wget https://kaldi-asr.org/models/3/0003_sre16_v2_1a.tar.gz 
tar -xzf 0001_aspire_chain_model.tar.gz -C ../models/
tar -xzf 0003_sre16_v2_1a.tar.gz -C ../models/
rm -rf temp
cd ..
# prepare the model
steps/online/nnet3/prepare_online_decoding.sh --mfcc-config conf/mfcc_hires.conf --online_cmvn_config models/exp/nnet3/extractor/online_cmvn.conf models/data/lang_chain models/exp/nnet3/extractor models/exp/chain/tdnn_7b models/exp/tdnn_7b_chain_online

utils/mkgraph.sh --self-loop-scale 1.0 models/data/lang_pp_test models/exp/tdnn_7b_chain_online models/exp/tdnn_7b_chain_online/graph_pp
 