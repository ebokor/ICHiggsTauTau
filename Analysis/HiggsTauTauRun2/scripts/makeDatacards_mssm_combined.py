#!/usr/bin/env python

# python scripts/makeDatacards_mssm_combined.py --years=2018 --name_changes --channels='tt,mt,et' --dry_run --batch
# python scripts/makeDatacards_mssm_combined.py --years=2018 --name_changes --channels='tt,mt,et'
# python scripts/makeDatacards_mssm_combined.py --years=2018 --name_changes --channels='tt,mt,et' --batch
# python scripts/makeDatacards_mssm_combined.py --years=2018 --name_changes --channels='tt,mt,et' --batch --syst
# python scripts/makeDatacards_mssm_combined.py --years=2018 --name_changes --channels='tt,mt,et' --batch --syst --dry_run

import sys
from optparse import OptionParser
import os
import string
import shlex
from subprocess import Popen, PIPE

CHANNELS = ['et', 'mt', 'em','tt']


config_files = {'2016':'scripts/plot_mssm_2016.cfg',
                '2017':'scripts/plot_mssm_2017.cfg',
                '2018':'scripts/plot_mssm_2018.cfg'
               }
param_files = {'2016':'scripts/params_mssm_2016.json',
               '2017':'scripts/params_mssm_2017.json',
               '2018':'scripts/params_mssm_2018.json',
              }

datacard_base = '/vols/cms/gu18/NewCombineCMSSW/CMSSW_10_2_21/src/CombineHarvester/MSSMvsSMRun2Legacy'
cmssw_base = '/vols/cms/gu18/CrabCMSSW/CMSSW_10_2_19'

def validate_channel(channel):
  assert channel in CHANNELS, 'Error, channel %(channel)s duplicated or unrecognised' % vars()
  CHANNELS.remove(channel)

def split_callback(option, opt, value, parser):
  setattr(parser.values, option.dest, value.split(','))

def run_command(command):
    print command
    p = Popen(shlex.split(command), stdout = PIPE, stderr = PIPE)
    out, err = p.communicate()
    print out, err
    return out, err

def name_changes(out_fold,ch,dc,ANA,dc_app,output,year):


    if year == "2016":
        ggh_masses=['80','90','100','110','120','130','140','160','180','200','250','300','350','400','450','500','600','700','800','900','1000','1200','1400','1500','1600','1800','2000','2300','2600','2900','3200']
        bbh_nlo_masses=['80','90','110','120','130','140','160','180','200','250','350','400','450','500','600','700','800','900','1000','1200','1400','1600','1800','2000','2300','2600','2900','3200']
    elif year == "2017":
        ggh_masses=['80','90','100','110','120','130','140','180','250','300','350','400','450','600','700','800','900','1200','1400','1500','1600','1800','2000','2300','2600','2900','3200']
        bbh_nlo_masses=['80','90','110','120','125','130','140','160','180','200','250','300','350','400','450','500','600','700','800','900','1000','1200','1400','1600','1800','2000','2300','2600','2900','3200','3500']
    elif year == "2018":
      ggh_masses = ['80','90','100','110','120','130','140','160','180','200','250','300','400','450','600','700','800','1200','1400','1500','1600','1800','2000','2600','2900','3200']
      bbh_nlo_masses = ['80','90','100','110','120','125','130','140','160','180','200','250','300','350','400','450','500','600','700','800','900','1000','1200','1400','1600','1800','2000','2300','2600','2900','3200','3500']

    print "Making histogram name changes:"

    output_name = '%(out_fold)s/htt_%(ch)s_%(dc)s.inputs-%(ANA)s%(dc_app)s%(output)s.root' % vars()
    nodename = '%(ch)s_%(dc)s' % vars()
    hist_name_changes = {'EmbedZTT':'EMB','EmbedZTT.subnodes':'EMB.subnodes',
                         'VV':'VVL',
                         'TT':'TTL',
                        }
    print("Making directory VVL.subnodes")
    print('rootmkdir {}:{}/VVL.subnodes'.format(output_name,nodename))
    os.system('rootmkdir {}:{}/VVL.subnodes'.format(output_name,nodename))
    print("VVT.subnodes/* -> VVL.subnodes/")
    os.system('rootmv {}:{}/VVT.subnodes/* {}:{}/VVL.subnodes/'.format(output_name,nodename,output_name,nodename))
    print("Removing VVT.subnodes")
    os.system('rootrm -r {}:{}/VVT.subnodes'.format(output_name,nodename))
    print("Removing VVT")
    os.system('rootrm {}:{}/VVT'.format(output_name,nodename))

    print("Making directory TTL.subnodes")
    os.system('rootmkdir {}:{}/TTL.subnodes'.format(output_name,nodename))
    print("TTT.subnodes/* -> TTL.subnodes/")
    os.system('rootmv {}:{}/TTT.subnodes/* {}:{}/TTL.subnodes/'.format(output_name,nodename,output_name,nodename))
    print("Removing TTT.subnodes")
    os.system('rootrm -r {}:{}/TTT.subnodes'.format(output_name,nodename))
    print("Removing TTT")
    os.system('rootrm {}:{}/TTT'.format(output_name,nodename))

    if ch == 'em':
        print("VVJ.subnodes/* -> VVL.subnodes/")
        os.system('rootmv {}:{}/VVJ.subnodes/* {}:{}/VVL.subnodes/'.format(output_name,nodename,output_name,nodename))
        print("Removing VVJ.subnodes")
        os.system('rootrm -r {}:{}/VVJ.subnodes'.format(output_name,nodename))
        print("Removing VVJ")
        os.system('rootrm {}:{}/VVJ'.format(output_name,nodename))
        print("TTJ.subnodes/* -> TTL.subnodes/")
        os.system('rootmv {}:{}/TTJ.subnodes/* {}:{}/TTL.subnodes/'.format(output_name,nodename,output_name,nodename))
        print("Removing TTJ.subnodes")
        os.system('rootrm -r {}:{}/TTJ.subnodes'.format(output_name,nodename))
        print("Removing TTJ")
        os.system('rootrm {}:{}/TTJ'.format(output_name,nodename))
        hist_name_changes["ZLL"] = "ZL"
        hist_name_changes["ZLL.subnodes"] = "ZL.subnodes"
    else:
        os.system('rootrm {}:{}/ZLL'.format(output_name,nodename))

    for mass in ggh_masses:
        for X in ['h','H','A']:
            for Y in ['t','b','i']:
                key_X_Y = "ggX_Y*".replace("*",mass).replace("X",X).replace("Y",Y)
                val_X_Y = "ggX_Y_*".replace("*",mass).replace("X",X).replace("Y",Y)
                hist_name_changes[key_X_Y] = val_X_Y
        key_ggh = "ggH*".replace("*",mass)
        val_ggh = "ggH_*".replace("*",mass)
        hist_name_changes[key_ggh] = val_ggh
    for mass in bbh_nlo_masses:
        key_bbh = "bbH*".replace("*",mass)
        val_bbh = "bbH_*".replace("*",mass)
        hist_name_changes[key_bbh] = val_bbh

    for key, value in hist_name_changes.items():
        print key," -> ",value
        command = "rootmv {}:{}/{} {}:{}/{}".format(output_name,nodename,key,output_name,nodename,value)
        os.system(command)   

parser = OptionParser()
parser.add_option("-i","--input", dest="folder", type='string', default='',
                  help="The input folder, containing the output of HTT - can be used to override config file")
parser.add_option("-o","--output", dest="output", type='string', default='',
                  help="The name that will be appended to the datacard inputs.")
parser.add_option("--output_folder", dest="output_folder", type='string', default='./',
                  help="Output folder where plots/datacards will be saved to.")
parser.add_option("-c", "--channels", dest="channels", type='string', action='callback',callback=split_callback,
                  help="A comma separated list of channels to process.  Supported channels: %(CHANNELS)s" % vars())
parser.add_option("-e", dest="energy", type='string', default='13',
                  help="The C.O.M. energy is written into the datacard name, default is 13")
parser.add_option("--batch", dest="batch", action='store_true', default=False,
                  help="Submit on batch.")
parser.add_option("--batch_name_changes", dest="batch_name_changes", action='store_true', default=False,
                  help="Submit on batch.")
parser.add_option("--dry_run",dest="dry_run", action='store_true', default=False,
                  help="Just displays code it will run")
parser.add_option("--name_changes",dest="name_changes", action='store_true', default=False,
                  help="Does name changes")
parser.add_option("--years", dest="years", type='string', default='2016,2017,2018',
                  help="Year input")
parser.add_option("--cat", dest="cat", type='string', default='medium',
                  help="Category to do name change for")
parser.add_option("--out_fold", dest="out_fold", type='string', default='',
                  help="Output folder for name changes")
parser.add_option("--syst",dest="syst", action='store_true', default=False,
                  help="Run with systematics")




(options, args) = parser.parse_args()
output_folder = options.output_folder
output = options.output
if output: 
  output = '-'+output
  print 'Appending "%(output)s" to datacard outputs' % vars()

channels = options.channels
years = options.years
syst = options.syst

print 'Processing channels:      %(channels)s' % vars()
print 'Processing years:         %(years)s' % vars()

years = options.years.split(',')

if not options.batch_name_changes:
 
  for year in years:
   
    CFG = config_files[year]
    COM = options.energy

    with open("%(CFG)s"%vars(),"r") as cfgfile:
        lines = cfgfile.readlines()

    configmap={}

    for ind in range(0,len(lines)):
        if len(lines[ind].split("="))>1:
            configmap[lines[ind].split("=")[0]]=(lines[ind].split("=")[1])
    if "signal_scheme" in configmap:
        SCHEME= configmap["signal_scheme"].rstrip('\n')
    YEAR=year
    FOLDER=configmap["folder"].rstrip('\n')
    PARAMS=configmap["paramfile"].rstrip('\n')

    PARAMS = param_files[year]

    ########## Set up schemes and options

    extra_global = ' '

    BINS_FINE="[0,10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200,225,250,275,300,325,350,400,500,700,900,1100,1300,1500,1700,1900,2100,2300,2500,2700,2900,3100,3300,3500,3700,3900]"
    BINS="[0,20,40,60,80,100,120,140,160,180,200,250,300,350,400,500,700,900,1100,1300,1500,1700,1900,2100,2300,2500,2700,2900,3100,3300,3500,3700,3900]"

    categories_et = [
                     "inclusive",
                     "nobtag_tightmt",
                     "nobtag_loosemt",
                     "btag_tightmt",
                     "btag_loosemt",
    ]

    categories_mt = [
                     "inclusive",
                     "nobtag_tightmt",
                     "nobtag_loosemt",
                     "btag_tightmt",
                     "btag_loosemt",
    ]

    categories_tt = [
                     "inclusive",
                     "btag",
                     "nobtag",
    ]

    categories_em = [
                     "inclusive",
                     "nobtag_highdzeta",
                     "nobtag_mediumdzeta",
                     "nobtag_lowdzeta",
                     "btag_highdzeta",
                     "btag_mediumdzeta",
                     "btag_lowdzeta",
                     "ttbar_control",
    ]
 
    ANA = 'mssm-vs-sm-Run%(year)s' % vars()

    cat_schemes = {
      'et' : categories_et,
      'mt' : categories_mt,
      'em' : categories_em,
      'tt' : categories_tt
    }

    ### Systematics ###

    common_shape_systematics = [
      ' --syst_tau_id_diff="CMS_eff_t_*_%(year)s"' % vars(), # Tau ID efficiency
      ' --syst_tau_trg_diff="CMS_eff_*_%(year)s"' % vars(), # Tau Trigger efficiency
      ' --syst_tau_scale_grouped="CMS_scale_t_*group_%(year)s"' % vars(), # Tau energy scale
      ' --syst_tquark="CMS_htt_ttbarShape"', # Top pT re-weighting
      ' --syst_res_j="CMS_res_j_%(year)s"' % vars(), # Jet energy resolution
      ' --syst_scale_met_unclustered="CMS_scale_met_unclustered_%(year)s"' % vars(), # MET unclustered energy uncertainty
      ' --syst_scale_met="CMS_htt_boson_scale_met_%(year)s"' % vars(), # MET recoil correction uncertainty
      ' --syst_res_met="CMS_htt_boson_reso_met_%(year)s"' % vars(),  # MET recoil correction uncertainty
      ' --syst_scale_j_regrouped="CMS_scale_j_*group"', # Jet energy scale (grouped)
      ' --syst_embedding_tt="CMS_htt_emb_ttbar_%(year)s"' % vars(), # ttbar contamination in embedding
    ]

    if year != '2018': 
      common_shape_systematics += [
        ' --syst_prefire="CMS_prefiring"'
      ]
    if year == '2016':  
      common_shape_systematics += [
        ' --syst_zwt="CMS_htt_dyShape_2016"'
      ]
    else:
      common_shape_systematics += [
        ' --syst_zwt="CMS_htt_dyShape"'
      ]


    # need lepton trigger efficiency
    et_shape_systematics = [
      ' --syst_efake_0pi_scale="CMS_ZLShape_et_1prong_%(year)s"' % vars(), # l to tau h fake energy scale
      ' --syst_efake_1pi_scale="CMS_ZLShape_et_1prong1pizero_%(year)s"' % vars(), # l to tau h fake energy scale
      ' --syst_e_scale="CMS_scale_e"', # Election energy scale
      ' --syst_lep_trg_diff="CMS_eff_*_%(year)s"' % vars(), # Lepton trigger efficiency 
      ' --do_ff_systs' 
    ]

    mt_shape_systematics = [
      ' --syst_mufake_0pi_scale="CMS_ZLShape_mt_1prong_%(year)s"' % vars(), # l to tau h fake energy scale
      ' --syst_mufake_1pi_scale="CMS_ZLShape_mt_1prong1pizero_%(year)s"' % vars(), # l to tau h fake energy scale
      ' --syst_lep_trg_diff="CMS_eff_*_%(year)s"' % vars(), # Lepton trigger efficiency 
      ' --do_ff_systs'
    ]

    tt_shape_systematics = [
      ' --do_ff_systs'
    ]
   
    em_shape_systematics = ['']

    extra_channel = {
        "em" : common_shape_systematics+em_shape_systematics,
        "et" : common_shape_systematics+et_shape_systematics,
        "mt" : common_shape_systematics+mt_shape_systematics,
        "tt" : common_shape_systematics+tt_shape_systematics,
    }


    var     = 'mt_tot'
    dc_app  = '-mttot'

    add_cond = '--singletau --add_wt=\'wt_tau_trg_mssm*wt_tau_id_mssm*wt_prefire\''

    for ch in channels:
      categories = cat_schemes[ch]

      out_fold = '%(datacard_base)s/shapes/%(year)s/%(ch)s' % vars()


      for cat in categories:
        if ch == "em": method = '19'
        else: method = '17'

        if cat.startswith("btag"): bins = BINS
        else: bins = BINS_FINE

        if syst:
          for i in extra_channel[ch]:   
            add_cond += i

        run_cmd = 'python %(cmssw_base)s/src/UserCode/ICHiggsTauTau/Analysis/HiggsTauTauRun2/scripts/HiggsTauTauPlot.py --cfg=%(CFG)s --channel=%(ch)s --method=%(method)s --cat=%(cat)s --year=%(YEAR)s --outputfolder=%(output_folder)s/ --datacard=%(cat)s --paramfile=%(PARAMS)s --folder=%(FOLDER)s --var="%(var)s%(bins)s" --embedding --doMSSMReWeighting --add_sm_background=125 --no_plot %(add_cond)s' % vars()
        hadd_cmd = 'hadd -f %(out_fold)s/htt_%(ch)s_%(cat)s.inputs-%(ANA)s%(dc_app)s%(output)s.root %(output_folder)s/datacard_*_%(cat)s_%(ch)s_%(YEAR)s.root' % vars()
        rm_dc_cmd = 'rm %(output_folder)s/datacard_*_%(cat)s_%(ch)s_%(YEAR)s.root' % vars()      

        if not options.batch:
          print run_cmd
          if not options.dry_run:
            os.system(run_cmd)
            os.system(hadd_cmd)
            os.system(rm_dc_cmd)
            if options.name_changes:
              name_changes(out_fold,ch,cat,ANA,dc_app,output,year)
        elif options.batch:
          job_file = 'jobs/mssm_datacard_%(cat)s_%(ch)s_%(YEAR)s.sh' % vars()
          if os.path.exists(job_file): os.system('rm %(job_file)s' % vars())
          os.system('echo "#!/bin/bash" >> %(job_file)s' % vars())
          os.system('echo "cd %(cmssw_base)s/src/UserCode/ICHiggsTauTau/Analysis/HiggsTauTauRun2" >> %(job_file)s' % vars())
          os.system('echo "source /vols/grid/cms/setup.sh" >> %(job_file)s' % vars()) 
          os.system('echo "export SCRAM_ARCH=slc6_amd64_gcc481" >> %(job_file)s' % vars())
          os.system('echo "eval \'scramv1 runtime -sh\'" >> %(job_file)s' % vars())
          os.system('echo "source %(cmssw_base)s/src/UserCode/ICHiggsTauTau/Analysis/HiggsTauTauRun2/scripts/setup_libs.sh" >> %(job_file)s' % vars())
          os.system('echo "ulimit -c 0" >> %(job_file)s' % vars())
          os.system('echo "%(run_cmd)s" >> %(job_file)s' % vars())
          os.system('echo "%(hadd_cmd)s" >> %(job_file)s' % vars())
          os.system('echo "%(rm_dc_cmd)s" >> %(job_file)s' % vars())
          os.system('echo "python %(cmssw_base)s/src/UserCode/ICHiggsTauTau/Analysis/HiggsTauTauRun2/scripts/makeDatacards_mssm_combined.py --batch_name_changes --channels=%(ch)s --years=%(YEAR)s --cat=%(cat)s --out_fold=%(out_fold)s" >> %(job_file)s' % vars())
          os.system('chmod +x %(job_file)s' % vars())
          if not options.dry_run:
            error_file = job_file.replace('.sh','_error.log')
            output_file = job_file.replace('.sh','_output.log')
            if os.path.exists(error_file): os.system('rm %(error_file)s' % vars())
            if os.path.exists(output_file): os.system('rm %(output_file)s' % vars())
            os.system('qsub -e %(error_file)s -o %(output_file)s -V -q hep.q -l h_rt=10:0:0 -cwd %(job_file)s' % vars())
           
else:
    year = options.years 
    ch = options.channels[0]
    cat = options.cat
    dc_app  = '-mttot'
    out_fold = options.out_fold
    ANA = 'mssm-vs-sm-Run%(year)s' % vars()
    name_changes(out_fold,ch,cat,ANA,dc_app,output,year)
    


