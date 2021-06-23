mkdir -p temp
cd temp
wget https://kaldi-asr.org/models/1/0001_aspire_chain_model.tar.gz
tar -xzf 0001_aspire_chain_model.tar.gz
mv exp ..
mv data ..
cd ..
# prepare the model
steps/online/nnet3/prepare_online_decoding.sh \
  --mfcc-config conf/mfcc_hires.conf data/lang_chain exp/nnet3/extractor exp/chain/tdnn_7b exp/tdnn_7b_chain_online

utils/mkgraph.sh --self-loop-scale 1.0 data/lang_pp_test exp/tdnn_7b_chain_online exp/tdnn_7b_chain_online/graph_pp