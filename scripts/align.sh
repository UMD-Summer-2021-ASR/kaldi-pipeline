#!/bin/bash
source ../path.sh

# input transcript (can be nbest)
input_trans=$1
# input wave file
input_wav=$2

input_lang_dir=$3

# ctm file contains the aligned trancript
out_ctm=$4

out_phone_ctm=$5

out_state_seq=$6

likelihod_per_frame=$7

out_vtt=$8

workdir=$9

modeldir=${10}


# create scp files
python scripts/create_scp.py -i $input_wav -o $9




# copy the lm data
mkdir -p $workdir/lang

mkdir -p $workdir/graph_pp


cp -rf $input_lang_dir/*  $workdir/lang


# expand and update the transcriptions
python scripts/convert_trans.py -i $input_trans -o  $workdir/trans.txt \
        -l [laughter] -n [noise] -u "<unk>" -w  $workdir/lang/words.txt 

# make sure srilm is installed in is in the path (path.sh should do it but in case it does not)
ngram-count   -text $9/trans.txt -order 2 -addsmooth 0.1   -unk  -lm  $workdir/custom.lm



#sh test.sh
# create a FST for custom lm (G.fst)
cat $workdir/custom.lm  | arpa2fst --disambig-symbol=#0  --read-symbol-table=$9/lang/words.txt - $9/lang/G.fst

# create HCLG graph
# utils/mkgraph.sh --self-loop-scale 1.0 $workdir/lang exp/tdnn_7b_chain_online $9/graph_pp


# run the recognizer
# subsample the frames by factor 3
# --frame-subsampling-factor=1
mkdir -p $workdir/out
online2-wav-nnet3-latgen-faster --online=true --do-endpointing=false   --config=${10}/conf/online.conf --max-active=7000 --beam=15.0 \
--lattice-beam=6.0 --acoustic-scale=1.0 --word-symbol-table=${10}/graph_pp/words.txt ${10}/final.mdl \
${10}/graph_pp/HCLG.fst "ark:$9/spk2utt.scp"  "scp:$9/wav.scp" "ark:|lattice-scale --acoustic-scale=0.5 ark:- ark:- | gzip -c >$9/out/lat.1.gz" > $9/recog_logs 2>&1

python scripts/extract_likelihood_per_frame.py $9/recog_logs $likelihod_per_frame
# create time alignment
# also acount for frame sub-sampling
# --frame-shift=0.01
lattice-align-words-lexicon  $9/lang/phones/align_lexicon.int  ${10}/final.mdl "ark:gunzip -c $9/out/lat.1.gz|" ark:- | lattice-1best ark:- ark:- |  nbest-to-ctm  ark:- $9/out/align.ctm

zcat $9/out/lat.1.gz  > $9/out/lat.1
lattice-1best --acoustic-scale=1 ark:$9/out/lat.1 ark:$9/out/1best.lats
nbest-to-linear ark:$9/out/1best.lats ark,t:$9/out/1.ali 
ali-to-phones --ctm-output ${10}/final.mdl ark:$9/out/1.ali $9/out/phone_alined.ctm

python scripts/convert_ctm.py -i $9/out/align.ctm  -w $9/lang/words.txt -o $out_ctm

python scripts/convert_ctm.py -i $9/out/phone_alined.ctm  -w $9/lang/phones.txt -o $out_phone_ctm

copy-int-vector ark:$9/out/1.ali ark,t:$9/out/transids.txt
show-transitions $9/lang/phones.txt ${10}/final.mdl >  $9/out/transitions.txt
python scripts/map_kaldi_transitionids.py  --input $9/out/transids.txt  --input_transitions $9/out/transitions.txt  --output $out_state_seq
python scripts/convert_vtt.py --input_ctm $out_ctm --output_vtt $out_vtt