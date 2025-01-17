#!/bin/sh

## Try and take the JOBWRAPPER and JOBSUBMIT commands
## from the environment if set, otherwise use these defaults
: ${JOBWRAPPER:="./scripts/generate_job.sh"}
: ${JOBSUBMIT:="eval"}

#export JOBSUBMIT="./scripts/submit_ic_batch_job.sh hepmedium.q"

JOBSCRIPT="./scripts/submit_ic_batch_job.sh" 
JOBQUEUE="hepshort.q"
export JOBSUBMIT=$JOBSCRIPT" "$JOBQUEUE


echo "Using job-wrapper: " $JOBWRAPPER
echo "Using job-submission: " $JOBSUBMIT

CONFIG=scripts/DefaultConfig.cfg
PRODUCTION=Dec18

for METCUT in 130
  do
  for CHANNEL in nunu nunulowmet nunuiglep nunulowmetiglep #nunuiglep  mumu #nunu enu munu taunu #mumu nunuiglep
    do
    for SYST in central #JESUP JESDOWN JERBETTER JERWORSE #NOTE SYSTEMATIC RUNS WILL BE SAME AS CENTRAL BUT OUTPUT WILL GO TO SYSTEMATIC SUBDIRECTORIES
      do
      SYSTOPTIONS="--dojessyst=false --dojersyst=false" 
      JOBDIRPREFIX=jobs_rerecogenqcd
      JOBDIR=$JOBDIRPREFIX/$CHANNEL/MET$METCUT/
      OUTPUTPREFIX=output_rerecogenqcd
      OUTPUTDIR=$OUTPUTPREFIX/$CHANNEL/MET$METCUT/
      
      if [ "$SYST" = "JESUP" ]
	  then
	  SYSTOPTIONS="--dojessyst=true --jesupordown=true"
	  JOBDIR=$JOBDIRPREFIX/$CHANNEL/MET$METCUT/JESUP/
	  OUTPUTDIR=$OUTPUTPREFIX/$CHANNEL/MET$METCUT/JESUP/
      fi
      
      if [ "$SYST" = "JESDOWN" ]
	  then
	  SYSTOPTIONS="--dojessyst=true --jesupordown=false"
	  JOBDIR=$JOBDIRPREFIX/$CHANNEL/MET$METCUT/JESDOWN/
	  OUTPUTDIR=$OUTPUTPREFIX/$CHANNEL/MET$METCUT/JESDOWN/
      fi  

      if [ "$SYST" = "JERBETTER" ]
	  then
	  SYSTOPTIONS="--dojessyst=false --dojersyst=true --jerbetterorworse=true"
	  JOBDIR=$JOBDIRPREFIX/$CHANNEL/MET$METCUT/JERBETTER/
	  OUTPUTDIR=$OUTPUTPREFIX/$CHANNEL/MET$METCUT/JERBETTER/
      fi  

      if [ "$SYST" = "JERWORSE" ]
	  then
	  SYSTOPTIONS="--dojessyst=false --dojersyst=true --jerbetterorworse=false"
	  JOBDIR=$JOBDIRPREFIX/$CHANNEL/MET$METCUT/JERWORSE/
	  OUTPUTDIR=$OUTPUTPREFIX/$CHANNEL/MET$METCUT/JERWORSE/
      fi  


      
      
      echo "Config file: $CONFIG"
      mkdir -p $JOBDIR
      mkdir -p $OUTPUTDIR
      
      for QUEUEDIR in short medium long
	do
	
	if [ "$QUEUEDIR" = "long" ]
	    then
	    JOBQUEUE="heplong.q"
	    export JOBSUBMIT=$JOBSCRIPT" "$JOBQUEUE
	    echo "Using job-submission: " $JOBSUBMIT
	elif [ "$QUEUEDIR" = "medium" ]
	    then
	    JOBQUEUE="hepmedium.q"
	    export JOBSUBMIT=$JOBSCRIPT" "$JOBQUEUE
	    echo "Using job-submission: " $JOBSUBMIT
	else
	    JOBQUEUE="hepshort.q"
	    export JOBSUBMIT=$JOBSCRIPT" "$JOBQUEUE
	    echo "Using job-submission: " $JOBSUBMIT
	fi
	
	PREFIX=root://xrootd.grid.hep.ph.ic.ac.uk//store/user/pdunne/$PRODUCTION/MET/
	
	for FILELIST in `ls filelists/$PRODUCTION/$QUEUEDIR/${PRODUCTION}_MET_*`
	  do
	  echo "Processing files in "$FILELIST
	  
	  echo $FILELIST > tmp.txt
	  sed "s/filelists\/${PRODUCTION}\/$QUEUEDIR\/${PRODUCTION}_MET_//" tmp.txt > tmp2.txt
	  
	  JOB=MET_`sed "s/\.dat//" tmp2.txt`
	  
	  rm tmp.txt tmp2.txt
	  
	  echo "JOB name = $JOB"
	  
	  $JOBWRAPPER "./bin/HiggsNuNu --cfg=$CONFIG --filelist="$FILELIST" --input_prefix=$PREFIX --output_name=$JOB.root --output_folder=$OUTPUTDIR --met_cut=$METCUT $SYSTOPTIONS --channel=$CHANNEL &> $JOBDIR/$JOB.log" $JOBDIR/$JOB.sh
	  $JOBSUBMIT $JOBDIR/$JOB.sh
	  
	done
	
      done
      
    done
    
  done
  
done

#if (( "$#" != "2" ))
#then
#echo ""
#    exit
#fi

