#!/usr/bin/env python
import ROOT
import imp
import json
from array import array
import numpy as np
import subprocess
import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--year','-y', help= 'year', type=str, default='2017')
parser.add_argument('--channel','-c', help= 'channel', type=str, default='mt')
args = parser.parse_args()

year = args.year
channel = args.channel

crosstrg_pt = 0
if channel == 'mt':
  if year == '2016':
    crosstrg_pt = 23
  else:
    crosstrg_pt = 25
if channel == 'et':
  if year == '2016':
    crosstrg_pt = 25
  elif year == '2017':
    crosstrg_pt = 28
  elif year == '2018':
    crosstrg_pt = 33


cmssw_base = subprocess.check_output('echo $CMSSW_BASE', shell=True).replace('\n','')

wsptools = imp.load_source('wsptools', '%(cmssw_base)s/src/UserCode/ICHiggsTauTau/Analysis/HiggsTauTauRun2/scripts/workspaceTools.py' % vars())

def GetFromTFile(str):
    f = ROOT.TFile(str.split(':')[0])
    obj = f.Get(str.split(':')[1]).Clone()
    f.Close()
    return obj

# Boilerplate
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(ROOT.kTRUE)
ROOT.RooWorkspace.imp = getattr(ROOT.RooWorkspace, 'import')
ROOT.TH1.AddDirectory(0)

w = ROOT.RooWorkspace('w')

wp = 'medium'

# get fractions

loc = '%(cmssw_base)s/src/UserCode/ICHiggsTauTau/Analysis/HiggsTauTauRun2/ff_%(channel)s_%(year)s/' % vars()

histsToWrap = [(loc + 'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:%(channel)s_fracs_nbjets0_os_qcd' % vars(),   'lt_fracs_nbjets0_os_qcd' % vars()),
               (loc + 'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:%(channel)s_fracs_nbjets1_os_qcd' % vars(),   'lt_fracs_nbjets1_os_qcd' % vars()),
               (loc + 'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:%(channel)s_fracs_nbjets0_ss_qcd' % vars(),   'lt_fracs_nbjets0_ss_qcd' % vars()),
               (loc + 'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:%(channel)s_fracs_nbjets1_ss_qcd' % vars(),   'lt_fracs_nbjets1_ss_qcd' % vars()),
               (loc + 'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:%(channel)s_fracs_nbjets0_os_wjets' % vars(), 'lt_fracs_nbjets0_os_wjets' % vars()),
               (loc + 'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:%(channel)s_fracs_nbjets1_os_wjets' % vars(), 'lt_fracs_nbjets1_os_wjets' % vars()),
               (loc + 'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:%(channel)s_fracs_nbjets0_ss_wjets' % vars(), 'lt_fracs_nbjets0_ss_wjets' % vars()),
               (loc + 'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:%(channel)s_fracs_nbjets1_ss_wjets' % vars(), 'lt_fracs_nbjets1_ss_wjets' % vars()),
               (loc + 'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:%(channel)s_fracs_nbjets0_os_ttbar' % vars(), 'lt_fracs_nbjets0_os_ttbar' % vars()),
               (loc + 'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:%(channel)s_fracs_nbjets1_os_ttbar' % vars(), 'lt_fracs_nbjets1_os_ttbar' % vars()),
               (loc + 'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:%(channel)s_fracs_nbjets0_ss_ttbar' % vars(), 'lt_fracs_nbjets0_ss_ttbar' % vars()),
               (loc + 'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:%(channel)s_fracs_nbjets1_ss_ttbar' % vars(), 'lt_fracs_nbjets1_ss_ttbar' % vars()),
              ]

for task in histsToWrap:
   wsptools.SafeWrapHist(
     w, ['expr::mt_max120("min(119.9,@0)",mt[0])'],
     GetFromTFile(task[0]),
     name=task[1])

for i in ['qcd','wjets','ttbar']:
  w.factory('expr::lt_fracs_%(i)s_nom("(@0!=0)*((@1==0)*(@2)+(@1>=1)*@3)+(@0==0)*((@1==0)*(@4)+(@1>=1)*@5)", os[1],nbjets[0],lt_fracs_nbjets0_os_%(i)s,lt_fracs_nbjets1_os_%(i)s,lt_fracs_nbjets0_ss_%(i)s,lt_fracs_nbjets1_ss_%(i)s)' % vars())

  # if the fractions are set by the user then overwrite these values
  w.factory('expr::lt_fracs_%(i)s("(@0>=0)*@0 + (@0<0)*@1", %(i)s_frac[-1], lt_fracs_%(i)s_nom)' % vars())

w.factory('expr::pt_bounded("max(min(599.9,@0),20)",pt[0])' % vars())
w.factory('expr::pt_bounded140("max(min(139.9,@0),20)",pt[0])' % vars())

# pT dependent fits

jetpt_bins = [
            'jet_pt_low',
            'jet_pt_med',
            'jet_pt_high',
]


cutsmap_njets = {
                -1: '@0>=0',
                0: '@0==0',
                1: '@0>=1',
}

cutsmap_jetpt = {
            'jet_pt_low':'@1<1.25*@2',
            'jet_pt_med':'@1>=1.25*@2&&@1<1.5*@2',
            'jet_pt_high':'@1>=1.5*@2',
}

# get all fitted functions for raw fake factors and statistical uncertainties from fit uncertainty bands

for p in ['qcd','wjets','ttbar']:

  if p == 'ttbar': 
    njets_loop = [-1]
  else:
    njets_loop = [0,1]

  for njet in njets_loop:
    for jetpt in jetpt_bins:
 
      if p == 'ttbar':
        name='%(jetpt)s_inclusive_pt_2_ff_%(p)s_mc' % vars()
        short_name='%(jetpt)s_ttbar' % vars()
      else:
        name='%(jetpt)s_%(njet)ijet_pt_2_ff_%(p)s' % vars()
        short_name='%(jetpt)s_%(njet)ijet_%(p)s' % vars()
  
  
      func = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:%(name)s_fit' % vars())
      func_str=str(func.GetExpFormula('p')).replace('x','@0').replace(',false','')
      nparams = func.GetNpar() 
 
      w.factory('expr::lt_%(name)s_fit("max(%(func_str)s,0.)",pt_bounded)' % vars())
 
      if p == 'wjets' and njet==1:
        # if wjets and njets=1 we need to also get the function bounded at 140 for ttbar corrections and the corresponding MC function
        w.factory('expr::lt_%(name)s_pt140_fit("max(%(func_str)s,0.)",pt_bounded140)' % vars()) 
        name_mc = name.replace('wjets','wjets_mc')
        func_mc = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:%(name_mc)s_fit' % vars())
        func_str_mc=str(func.GetExpFormula('p')).replace('x','@0').replace(',false','')
        w.factory('expr::lt_%(name_mc)s_pt140_fit("max(%(func_str_mc)s,0.)",pt_bounded140)' % vars()) 

      # get stat uncertainties
      hist_nom = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:%(name)s_uncert' % vars())
      if p == 'ttbar':
        # for the ttbar the FF will be corrected by the ratio of Wdata/Wmc
        # for Wdata we will correlated properly the statistical uncertainties with the W FFs
        # for Wmc to reduce the number of statistical uncertainties we divide ttbar by Wmc and use the corresponding uncertainty band as the uncertainty on ttbar
        wmc_name='%(jetpt)s_1jet_pt_2_ff_wjets_mc' % vars()
        hist_nom_2 = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:%(wmc_name)s_uncert' % vars())
        firstflatbin = hist_nom_2.FindBin(140)
        maxval = hist_nom_2.GetBinContent(firstflatbin -1)
        maxerr = hist_nom_2.GetBinError(firstflatbin -1)
        for i in range(firstflatbin,hist_nom_2.GetNbinsX()+1):
          hist_nom_2.SetBinContent(i, maxval) 
          hist_nom_2.SetBinError(i, maxerr)
        hist_nom.Divide(hist_nom_2)    
      (uncert1_up, uncert1_down, uncert2_up, uncert_2_down) = wsptools.SplitUncert(hist_nom)
      wsptools.SafeWrapHist(w, ['pt_bounded'], hist_nom, name='lt_%(name)s_uncert_nom' % vars())
      wsptools.SafeWrapHist(w, ['pt_bounded'], uncert1_up, name='lt_%(name)s_uncert1_hist_up' % vars())
      wsptools.SafeWrapHist(w, ['pt_bounded'], uncert2_up, name='lt_%(name)s_uncert2_hist_up' % vars())

      njets_cut = cutsmap_njets[njet] % vars() 
      jetpt_cut    = cutsmap_jetpt[jetpt] % vars()
 
      if p == 'wjets' and njet==1:
        # if wjets and njets=1 we need to also get the function bounded at 140 for ttbar corrections
        wsptools.SafeWrapHist(w, ['pt_bounded140'], hist_nom,   name='lt_%(name)s_pt140_uncert_nom' % vars())
        wsptools.SafeWrapHist(w, ['pt_bounded140'], uncert1_up, name='lt_%(name)s_pt140_uncert1_hist_up' % vars())
        wsptools.SafeWrapHist(w, ['pt_bounded140'], uncert2_up, name='lt_%(name)s_pt140_uncert2_hist_up' % vars())

        w.factory('expr::lt_%(short_name)s_pt140_uncert1_up("(%(jetpt_cut)s)*(@3/@4) + ((%(jetpt_cut)s)==0)",njets[0],jetpt[40],pt_bounded,lt_%(name)s_pt140_uncert1_hist_up,lt_%(name)s_pt140_uncert_nom)' % vars())
        w.factory('expr::lt_%(short_name)s_pt140_uncert2_up("(%(jetpt_cut)s)*(@3/@4) + ((%(jetpt_cut)s)==0)",njets[0],jetpt[40],pt_bounded,lt_%(name)s_pt140_uncert2_hist_up,lt_%(name)s_pt140_uncert_nom)' % vars())
 
      if nparams <= 4: 
        w.factory('expr::lt_%(short_name)s_uncert1_up("(%(njets_cut)s&&%(jetpt_cut)s)*(@3/@4) + ((%(njets_cut)s&&%(jetpt_cut)s)==0)",njets[0],jetpt[40],pt_bounded,lt_%(name)s_uncert1_hist_up,lt_%(name)s_uncert_nom)' % vars())
        w.factory('expr::lt_%(short_name)s_uncert2_up("(%(njets_cut)s&&%(jetpt_cut)s)*(@3/@4) + ((%(njets_cut)s&&%(jetpt_cut)s)==0)",njets[0],jetpt[40],pt_bounded,lt_%(name)s_uncert2_hist_up,lt_%(name)s_uncert_nom)' % vars())
        w.factory('expr::lt_%(short_name)s_uncert3_up("(%(njets_cut)s&&%(jetpt_cut)s&&@2>200)*1.5 + ((%(njets_cut)s&&%(jetpt_cut)s&&@2>200)==0)",njets[0],jetpt[40],pt_bounded)' % vars())
        w.factory('expr::lt_%(short_name)s_uncert4_up("1",njets[0],jetpt[40],pt_bounded)' % vars()) # for convinience always add a uncert4 even if it is not needed (=1)
      elif nparams == 6:
        w.factory('expr::lt_%(short_name)s_uncert1_up("(%(njets_cut)s&&%(jetpt_cut)s&&@2<140)*(@3/@4) + ((%(njets_cut)s&&%(jetpt_cut)s&&@2<140)==0)",njets[0],jetpt[40],pt_bounded,lt_%(name)s_uncert1_hist_up,lt_%(name)s_uncert_nom)' % vars())
        w.factory('expr::lt_%(short_name)s_uncert2_up("(%(njets_cut)s&&%(jetpt_cut)s&&@2<140)*(@3/@4) + ((%(njets_cut)s&&%(jetpt_cut)s&&@2<140)==0)",njets[0],jetpt[40],pt_bounded,lt_%(name)s_uncert2_hist_up,lt_%(name)s_uncert_nom)' % vars())
        w.factory('expr::lt_%(short_name)s_uncert3_up("(%(njets_cut)s&&%(jetpt_cut)s&&@2>=140&&@2<200)*(@3/@4) + ((%(njets_cut)s&&%(jetpt_cut)s&&@2>=140&&@2<200)==0)",njets[0],jetpt[40],pt_bounded,lt_%(name)s_uncert2_hist_up,lt_%(name)s_uncert_nom)' % vars())
        w.factory('expr::lt_%(short_name)s_uncert4_up("(%(njets_cut)s&&%(jetpt_cut)s&&@2>=200)*(@3/@4) + ((%(njets_cut)s&&%(jetpt_cut)s&&@2>=200)==0)",njets[0],jetpt[40],pt_bounded,lt_%(name)s_uncert2_hist_up,lt_%(name)s_uncert_nom)' % vars())

      elif nparams ==5:
        # for nparams 5 we have 2 possibilities: either the 140-200 and >200 bins have been merged with a single uncertainty or they are not merged and we have a single uncertainty only for the >200 bin
        # we need to determine whether or not the 140-200 and >200 bins are merged or not
        merged = '>=140' in func_str
#<ROOT.TF1 object ("jet_pt_med_inclusive_pt_2_ff_ttbar_mc_fit") at 0x96dcc60>
        if merged: minpt = '140'
        else: minpt = '200'
        w.factory('expr::lt_%(short_name)s_uncert1_up("(%(njets_cut)s&&%(jetpt_cut)s&&@2<%(minpt)s)*(@3/@4) + ((%(njets_cut)s&&%(jetpt_cut)s&&@2<%(minpt)s)==0)",njets[0],jetpt[40],pt_bounded,lt_%(name)s_uncert1_hist_up,lt_%(name)s_uncert_nom)' % vars())
        w.factory('expr::lt_%(short_name)s_uncert2_up("(%(njets_cut)s&&%(jetpt_cut)s&&@2<%(minpt)s)*(@3/@4) + ((%(njets_cut)s&&%(jetpt_cut)s&&@2<%(minpt)s)==0)",njets[0],jetpt[40],pt_bounded,lt_%(name)s_uncert2_hist_up,lt_%(name)s_uncert_nom)' % vars())
        w.factory('expr::lt_%(short_name)s_uncert3_up("(%(njets_cut)s&&%(jetpt_cut)s&&@2>=%(minpt)s)*(@3/@4) + ((%(njets_cut)s&&%(jetpt_cut)s&&@2>=%(minpt)s)==0)",njets[0],jetpt[40],pt_bounded,lt_%(name)s_uncert2_hist_up,lt_%(name)s_uncert_nom)' % vars())
        w.factory('expr::lt_%(short_name)s_uncert4_up("1",njets[0],jetpt[40],pt_bounded)' % vars()) # for convinience always add a uncert4 even if it is not needed (=1)


      w.factory('expr::lt_%(short_name)s_uncert1_down("2.-@0", lt_%(short_name)s_uncert1_up)' % vars())
      w.factory('expr::lt_%(short_name)s_uncert2_down("2.-@0", lt_%(short_name)s_uncert2_up)' % vars())
      w.factory('expr::lt_%(short_name)s_uncert3_down("2.-@0", lt_%(short_name)s_uncert3_up)' % vars())
      w.factory('expr::lt_%(short_name)s_uncert4_down("2.-@0", lt_%(short_name)s_uncert4_up)' % vars())

# make njets / jetpt binned functions

for p in ['wjets','qcd']:

  w.factory('expr::ff_lt_%(p)s_raw("(@0==0)*((@1<1.25*@2)*@3 + (@1>=1.25*@2&&@1<1.5*@2)*@4 + (@1>=1.5*@2)*@5) + (@0>0)*((@1<1.25*@2)*@6 + (@1>=1.25*@2&&@1<1.5*@2)*@7 + (@1>=1.5*@2)*@8)", njets[0], jetpt[40], pt_bounded, lt_jet_pt_low_0jet_pt_2_ff_%(p)s_fit, lt_jet_pt_med_0jet_pt_2_ff_%(p)s_fit, lt_jet_pt_high_0jet_pt_2_ff_%(p)s_fit, lt_jet_pt_low_1jet_pt_2_ff_%(p)s_fit, lt_jet_pt_med_1jet_pt_2_ff_%(p)s_fit, lt_jet_pt_high_1jet_pt_2_ff_%(p)s_fit)' % vars())

w.factory('expr::ff_lt_ttbar_raw("(@0>=0)*((@1<1.25*@2)*@3 + (@1>=1.25*@2&&@1<1.5*@2)*@4 + (@1>=1.5*@2)*@5)", njets[0], jetpt[40], pt_bounded, lt_jet_pt_low_inclusive_pt_2_ff_ttbar_mc_fit, lt_jet_pt_med_inclusive_pt_2_ff_ttbar_mc_fit, lt_jet_pt_high_inclusive_pt_2_ff_ttbar_mc_fit)' % vars())

# apply qcd corrections

w.factory('expr::met_bounded("min(@0,199.9)",met[0])' % vars())
w.factory('expr::l_pt_bounded140("min(@0,139.9)",l_pt[20])' % vars())
w.factory('expr::l_pt_bounded160("min(@0,159.9)",l_pt[20])' % vars())
w.factory('expr::l_pt_bounded200("min(@0,199.9)",l_pt[20])' % vars())
w.factory('expr::l_pt_bounded250("min(@0,249.9)",l_pt[20])' % vars())

for njet in [0,1]:
  func_ss = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:met_%(njet)ijet_closure_qcd_fit' % vars())
  func_ss_str=str(func_ss.GetExpFormula('p')).replace('x','@0').replace(',false','')
  
  func_os_1 = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:pt_1_nbjets%(njet)i_tightmt_dr_to_ar_aiso_closure_qcd_fit' % vars())
  func_os_str_1=str(func_os_1.GetExpFormula('p')).replace('x','@0').replace(',false','')

  func_os_2 = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:pt_1_nbjets%(njet)i_loosemt_dr_to_ar_aiso_closure_qcd_fit' % vars())
  func_os_str_2=str(func_os_2.GetExpFormula('p')).replace('x','@0').replace(',false','')

  w.factory('expr::lt_qcd_ss_njets%(njet)i_correction("max(%(func_ss_str)s,0.)",met_bounded)' % vars())
  w.factory('expr::lt_qcd_os_nbjets%(njet)i_tightmt_correction("max(%(func_os_str_1)s,0.)",l_pt_bounded140)' % vars())
  w.factory('expr::lt_qcd_os_nbjets%(njet)i_loosemt_correction("max(%(func_os_str_2)s,0.)",l_pt_bounded140)' % vars())

  # get stat uncertainties

  hist_ss_nom = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:met_%(njet)ijet_closure_qcd_uncert' % vars())
  hist_os_nom_1 = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:pt_1_nbjets%(njet)i_tightmt_dr_to_ar_aiso_closure_qcd_uncert' % vars())
  hist_os_nom_2 = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:pt_1_nbjets%(njet)i_loosemt_dr_to_ar_aiso_closure_qcd_uncert' % vars())

  (uncert1_up, uncert1_down, uncert2_up, uncert_2_down) = wsptools.SplitUncert(hist_ss_nom)

  wsptools.SafeWrapHist(w, ['met_bounded'], hist_ss_nom, name='lt_qcd_ss_njets%(njet)i_correction_nom' % vars())
  wsptools.SafeWrapHist(w, ['met_bounded'], uncert1_up, name='lt_qcd_ss_njets%(njet)i_correction_uncert1_hist_up' % vars())
  wsptools.SafeWrapHist(w, ['met_bounded'], uncert2_up, name='lt_qcd_ss_njets%(njet)i_correction_uncert2_hist_up' % vars())

  (uncert1_up, uncert1_down, uncert2_up, uncert_2_down) = wsptools.SplitUncert(hist_os_nom_1)

  wsptools.SafeWrapHist(w, ['l_pt_bounded140'], hist_os_nom_1, name='lt_qcd_os_nbjets%(njet)i_tightmt_correction_nom' % vars())
  wsptools.SafeWrapHist(w, ['l_pt_bounded140'], uncert1_up,     name='lt_qcd_os_nbjets%(njet)i_tightmt_correction_uncert1_hist_up' % vars())
  wsptools.SafeWrapHist(w, ['l_pt_bounded140'], uncert2_up,     name='lt_qcd_os_nbjets%(njet)i_tightmt_correction_uncert2_hist_up' % vars())
  
  (uncert1_up, uncert1_down, uncert2_up, uncert_2_down) = wsptools.SplitUncert(hist_os_nom_2)

  wsptools.SafeWrapHist(w, ['l_pt_bounded140'], hist_os_nom_2, name='lt_qcd_os_nbjets%(njet)i_loosemt_correction_nom' % vars())
  wsptools.SafeWrapHist(w, ['l_pt_bounded140'], uncert1_up,     name='lt_qcd_os_nbjets%(njet)i_loosemt_correction_uncert1_hist_up' % vars())
  wsptools.SafeWrapHist(w, ['l_pt_bounded140'], uncert2_up,     name='lt_qcd_os_nbjets%(njet)i_loosemt_correction_uncert2_hist_up' % vars())

  w.factory('expr::lt_qcd_ss_njets%(njet)i_correction_uncert1_up("@0/@1", lt_qcd_ss_njets%(njet)i_correction_uncert1_hist_up, lt_qcd_ss_njets%(njet)i_correction_nom)' % vars())
  w.factory('expr::lt_qcd_ss_njets%(njet)i_correction_uncert2_up("@0/@1", lt_qcd_ss_njets%(njet)i_correction_uncert2_hist_up, lt_qcd_ss_njets%(njet)i_correction_nom)' % vars())

  for x in ['loose', 'tight']:
    w.factory('expr::lt_qcd_os_nbjets%(njet)i_%(x)smt_correction_uncert1_up("@0/@1", lt_qcd_os_nbjets%(njet)i_%(x)smt_correction_uncert1_hist_up, lt_qcd_os_nbjets%(njet)i_%(x)smt_correction_nom)' % vars())
    w.factory('expr::lt_qcd_os_nbjets%(njet)i_%(x)smt_correction_uncert2_up("@0/@1", lt_qcd_os_nbjets%(njet)i_%(x)smt_correction_uncert2_hist_up, lt_qcd_os_nbjets%(njet)i_%(x)smt_correction_nom)' % vars())

w.factory('expr::lt_qcd_ss_correction("(@0==0)*@1 + (@0>0)*@2",njets[0], lt_qcd_ss_njets0_correction, lt_qcd_ss_njets1_correction )' % vars())
w.factory('expr::lt_qcd_os_correction("(@0==0)*((@1<50)*@2 + (@1>=50)*@3) + (@0>0)*((@1<50)*@4 + (@1>=50)*@5)", nbjets[0], mt[0], lt_qcd_os_nbjets0_tightmt_correction, lt_qcd_os_nbjets0_loosemt_correction, lt_qcd_os_nbjets1_tightmt_correction, lt_qcd_os_nbjets1_loosemt_correction )' % vars())

for i in [1,2]:

  w.factory('expr::lt_qcd_ss_correction_njets0_uncert%(i)i_up("(@0==0)*@1 + (@0!=0)", njets[0], lt_qcd_ss_njets0_correction_uncert%(i)i_up)' % vars())
  w.factory('expr::lt_qcd_ss_correction_njets1_uncert%(i)i_up("(@0==0) + (@0!=0)*@1", njets[0], lt_qcd_ss_njets1_correction_uncert%(i)i_up)' % vars())

  w.factory('expr::lt_qcd_os_correction_uncert%(i)i_up("(@0!=0)*((@1==0)*((@2<50)*@3 + (@2>=50)*@4) + (@1>0)*((@2<50)*@5 + (@2>=50)*@6)) + (@0==0) ",os[1], nbjets[0], mt[0], lt_qcd_os_nbjets0_tightmt_correction_uncert%(i)i_up, lt_qcd_os_nbjets0_loosemt_correction_uncert%(i)i_up, lt_qcd_os_nbjets1_tightmt_correction_uncert%(i)i_up, lt_qcd_os_nbjets1_loosemt_correction_uncert%(i)i_up)' % vars())

  w.factory('expr::lt_qcd_ss_correction_njets0_uncert%(i)i_down("2.-@0", lt_qcd_ss_correction_njets0_uncert%(i)i_up)' % vars())
  w.factory('expr::lt_qcd_ss_correction_njets1_uncert%(i)i_down("2.-@0", lt_qcd_ss_correction_njets1_uncert%(i)i_up)' % vars())
  w.factory('expr::lt_qcd_os_correction_uncert%(i)i_down("2.-@0", lt_qcd_os_correction_uncert%(i)i_up)' % vars())

# get final qcd fake factor
w.factory('expr::ff_lt_qcd("@0*@1*((@2!=0)*@3 + (@2==0))", ff_lt_qcd_raw, lt_qcd_ss_correction, os[1], lt_qcd_os_correction)' % vars())

qcd_systs=[]

# statistical uncertainties on measured qcd fake factors
# add statistical uncertainties 1 per njets/jetpt bin
for njet in [0,1]:
  for jetpt in jetpt_bins:
      short_name='%(jetpt)s_%(njet)ijet_qcd' % vars()
      for i in [1,2,3]:
        w.factory('expr::ff_lt_qcd_stat_njet%(njet)i_%(jetpt)s_unc%(i)i_up("@0*@1",ff_lt_qcd, lt_%(short_name)s_uncert%(i)i_up)' % vars())
        w.factory('expr::ff_lt_qcd_stat_njet%(njet)i_%(jetpt)s_unc%(i)i_down("@0*@1",ff_lt_qcd, lt_%(short_name)s_uncert%(i)i_down)' % vars())
        qcd_systs.append('qcd_stat_njet%(njet)i_%(jetpt)s_unc%(i)i' % vars())

# systematic uncertainty from applying os/ss correction twice or not applying it 
w.factory('expr::ff_lt_qcd_syst_up("@0*@1*((@2!=0)*@3*@3 + (@2==0))", ff_lt_qcd, lt_qcd_ss_correction, os[1], lt_qcd_os_correction)' % vars())
w.factory('expr::ff_lt_qcd_syst_down("@0*@1", ff_lt_qcd, lt_qcd_ss_correction, os[1])' % vars())
qcd_systs.append('qcd_syst')

## statistical uncertainties on os and ss closure corrections
for i in [1,2]:
#lt_qcd_os_correction_uncert%(i)i_up
  w.factory('expr::ff_lt_qcd_stat_ss_njets0_unc%(i)i_up("@0*@1", ff_lt_qcd, lt_qcd_ss_correction_njets0_uncert%(i)i_up)' % vars())
  w.factory('expr::ff_lt_qcd_stat_ss_njets0_unc%(i)i_down("@0*@1", ff_lt_qcd, lt_qcd_ss_correction_njets0_uncert%(i)i_down)' % vars())
  w.factory('expr::ff_lt_qcd_stat_ss_njets1_unc%(i)i_up("@0*@1", ff_lt_qcd, lt_qcd_ss_correction_njets1_uncert%(i)i_up)' % vars())
  w.factory('expr::ff_lt_qcd_stat_ss_njets1_unc%(i)i_down("@0*@1", ff_lt_qcd, lt_qcd_ss_correction_njets1_uncert%(i)i_down)' % vars())
  qcd_systs.append('qcd_stat_ss_njets0_unc%(i)i' % vars())
  qcd_systs.append('qcd_stat_ss_njets1_unc%(i)i' % vars())

  w.factory('expr::ff_lt_qcd_stat_os_unc%(i)i_up("@0*@1", ff_lt_qcd, lt_qcd_os_correction_uncert%(i)i_up)' % vars())
  w.factory('expr::ff_lt_qcd_stat_os_unc%(i)i_down("@0*@1", ff_lt_qcd, lt_qcd_os_correction_uncert%(i)i_down)' % vars())
  qcd_systs.append('qcd_stat_os_unc%(i)i' % vars())

print 'qcd systematics:'
print qcd_systs

#TODO: add systematics for W+jets subtraction when measuring QCD FFs

#################

# apply wjets corrections

#met in njets bins, pt in njets bins and low and high pT region, extrap in nbjets loose and tight mt (vs met)

for njet in [0,1]:
  func_met = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:met_%(njet)ijet_closure_wjets_fit' % vars())
  func_met_str=str(func_met.GetExpFormula('p')).replace('x','@0').replace(',false','')

  func_pt = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:high_pt_1_%(njet)ijet_closure_wjets_fit' % vars())
  if channel == 'et' and year == '2016':
    # if 2016 make a dummy function for low pT bins since we have no cross trigger anyway
    func_lowpt = ROOT.TF1(str(func_pt.GetName()).replace('high','low'), '1')
  else:
    func_lowpt = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:low_pt_1_%(njet)ijet_closure_wjets_fit' % vars())
  func_pt_str=str(func_pt.GetExpFormula('p')).replace('x','@0').replace(',false','')
  func_lowpt_str=str(func_lowpt.GetExpFormula('p')).replace('x','@0').replace(',false','')

  func_extrap_1 = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:met_nbjets%(njet)i_tightmt_dr_to_ar_closure_wjets_mc_fit' % vars())
  func_extrap_str_1=str(func_extrap_1.GetExpFormula('p')).replace('x','@0').replace(',false','')

  func_extrap_2 = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:met_nbjets%(njet)i_loosemt_dr_to_ar_closure_wjets_mc_fit' % vars())
  func_extrap_str_2=str(func_extrap_2.GetExpFormula('p')).replace('x','@0').replace(',false','')

  w.factory('expr::lt_wjets_met_njets%(njet)i_correction("max(%(func_met_str)s,0.)",met_bounded)' % vars())
  if njet ==0: w.factory('expr::lt_wjets_l_pt_njets%(njet)i_correction("max(%(func_pt_str)s,0.)",l_pt_bounded160)' % vars())
  else: w.factory('expr::lt_wjets_l_pt_njets%(njet)i_correction("max(%(func_pt_str)s,0.)",l_pt_bounded200)' % vars())
  w.factory('expr::lt_wjets_low_l_pt_njets%(njet)i_correction("max(%(func_lowpt_str)s,0.)",l_pt_bounded200)' % vars())
  w.factory('expr::lt_wjets_extrap_nbjets%(njet)i_tightmt_correction("max(%(func_extrap_str_1)s,0.)",met_bounded)' % vars())
  w.factory('expr::lt_wjets_extrap_nbjets%(njet)i_loosemt_correction("max(%(func_extrap_str_2)s,0.)",met_bounded)' % vars())

  # get stat uncertainties

  hist_met = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:met_%(njet)ijet_closure_wjets_uncert' % vars())
  hist_pt = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:high_pt_1_%(njet)ijet_closure_wjets_uncert' % vars())
  hist_extrap_1 = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:met_nbjets%(njet)i_tightmt_dr_to_ar_closure_wjets_mc_uncert' % vars())
  hist_extrap_2 = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:met_nbjets%(njet)i_loosemt_dr_to_ar_closure_wjets_mc_uncert' % vars())

  (uncert1_up, uncert1_down, uncert2_up, uncert_2_down) = wsptools.SplitUncert(hist_met)

  wsptools.SafeWrapHist(w, ['met_bounded'], hist_met, name='lt_wjets_met_njets%(njet)i_correction_nom' % vars())
  wsptools.SafeWrapHist(w, ['met_bounded'], uncert1_up, name='lt_wjets_met_njets%(njet)i_correction_uncert1_hist_up' % vars())
  wsptools.SafeWrapHist(w, ['met_bounded'], uncert2_up, name='lt_wjets_met_njets%(njet)i_correction_uncert2_hist_up' % vars())

  (uncert1_up, uncert1_down, uncert2_up, uncert_2_down) = wsptools.SplitUncert(hist_met)

  if njet ==0:
    wsptools.SafeWrapHist(w, ['l_pt_bounded160'], hist_pt, name='lt_wjets_l_pt_njets%(njet)i_correction_nom' % vars())
    wsptools.SafeWrapHist(w, ['l_pt_bounded160'], uncert1_up, name='lt_wjets_l_pt_njets%(njet)i_correction_uncert1_hist_up' % vars())
    wsptools.SafeWrapHist(w, ['l_pt_bounded160'], uncert2_up, name='lt_wjets_l_pt_njets%(njet)i_correction_uncert2_hist_up' % vars())
  else:
    wsptools.SafeWrapHist(w, ['l_pt_bounded200'], hist_pt, name='lt_wjets_l_pt_njets%(njet)i_correction_nom' % vars())
    wsptools.SafeWrapHist(w, ['l_pt_bounded200'], uncert1_up, name='lt_wjets_l_pt_njets%(njet)i_correction_uncert1_hist_up' % vars())
    wsptools.SafeWrapHist(w, ['l_pt_bounded200'], uncert2_up, name='lt_wjets_l_pt_njets%(njet)i_correction_uncert2_hist_up' % vars())

  (uncert1_up, uncert1_down, uncert2_up, uncert_2_down) = wsptools.SplitUncert(hist_extrap_1)

  wsptools.SafeWrapHist(w, ['met_bounded'], hist_extrap_1,  name='lt_wjets_extrap_nbjets%(njet)i_tightmt_correction_nom' % vars())
  wsptools.SafeWrapHist(w, ['met_bounded'], uncert1_up,     name='lt_wjets_extrap_nbjets%(njet)i_tightmt_correction_uncert1_hist_up' % vars())
  wsptools.SafeWrapHist(w, ['met_bounded'], uncert2_up,     name='lt_wjets_extrap_nbjets%(njet)i_tightmt_correction_uncert2_hist_up' % vars())

  (uncert1_up, uncert1_down, uncert2_up, uncert_2_down) = wsptools.SplitUncert(hist_os_nom_2)

  wsptools.SafeWrapHist(w, ['met_bounded'], hist_extrap_2,  name='lt_wjets_extrap_nbjets%(njet)i_loosemt_correction_nom' % vars())
  wsptools.SafeWrapHist(w, ['met_bounded'], uncert1_up,     name='lt_wjets_extrap_nbjets%(njet)i_loosemt_correction_uncert1_hist_up' % vars())
  wsptools.SafeWrapHist(w, ['met_bounded'], uncert2_up,     name='lt_wjets_extrap_nbjets%(njet)i_loosemt_correction_uncert2_hist_up' % vars())

  w.factory('expr::lt_wjets_met_njets%(njet)i_correction_uncert1_up("@0/@1", lt_wjets_met_njets%(njet)i_correction_uncert1_hist_up, lt_wjets_met_njets%(njet)i_correction_nom)' % vars())
  w.factory('expr::lt_wjets_met_njets%(njet)i_correction_uncert2_up("@0/@1", lt_wjets_met_njets%(njet)i_correction_uncert2_hist_up, lt_wjets_met_njets%(njet)i_correction_nom)' % vars())

  w.factory('expr::lt_wjets_l_pt_njets%(njet)i_correction_uncert1_up("@0/@1", lt_wjets_l_pt_njets%(njet)i_correction_uncert1_hist_up, lt_wjets_l_pt_njets%(njet)i_correction_nom)' % vars())
  w.factory('expr::lt_wjets_l_pt_njets%(njet)i_correction_uncert2_up("@0/@1", lt_wjets_l_pt_njets%(njet)i_correction_uncert2_hist_up, lt_wjets_l_pt_njets%(njet)i_correction_nom)' % vars())

  for x in ['loose', 'tight']:
    w.factory('expr::lt_wjets_extrap_nbjets%(njet)i_%(x)smt_correction_uncert1_up("@0/@1", lt_wjets_extrap_nbjets%(njet)i_%(x)smt_correction_uncert1_hist_up, lt_wjets_extrap_nbjets%(njet)i_%(x)smt_correction_nom)' % vars())
    w.factory('expr::lt_wjets_extrap_nbjets%(njet)i_%(x)smt_correction_uncert2_up("@0/@1", lt_wjets_extrap_nbjets%(njet)i_%(x)smt_correction_uncert2_hist_up, lt_wjets_extrap_nbjets%(njet)i_%(x)smt_correction_nom)' % vars())

w.factory('expr::lt_wjets_dr_correction("((@0==0)*@1 + (@0>0)*@2)*((@3<%(crosstrg_pt)s)*((@0==0)*@4 + (@0>0)*@5) + (@3>=%(crosstrg_pt)s)*((@0==0)*@6 + (@0>0)*@7))",njets[0], lt_wjets_met_njets0_correction, lt_wjets_met_njets1_correction, l_pt_bounded200, lt_wjets_low_l_pt_njets0_correction, lt_wjets_low_l_pt_njets1_correction, lt_wjets_l_pt_njets0_correction, lt_wjets_l_pt_njets1_correction )' % vars())
w.factory('expr::lt_wjets_extrap_correction("(@0>=70) + (@0<70&&@0>=50)*((@1==0)*@2 + (@1>0)*@3) + (@0<50)*((@1==0)*@4 + (@1>0)*@5)", mt[0], nbjets[0], lt_wjets_extrap_nbjets0_loosemt_correction, lt_wjets_extrap_nbjets1_loosemt_correction, lt_wjets_extrap_nbjets0_tightmt_correction, lt_wjets_extrap_nbjets1_tightmt_correction )' % vars())

for i in [1,2]:

  w.factory('expr::lt_wjets_met_correction_njets0_uncert%(i)i_up("(@0==0)*@1 + (@0!=0)", njets[0], lt_wjets_met_njets0_correction_uncert%(i)i_up)' % vars())
  w.factory('expr::lt_wjets_met_correction_njets1_uncert%(i)i_up("(@0==0) + (@0!=0)*@1", njets[0], lt_wjets_met_njets1_correction_uncert%(i)i_up)' % vars())
  w.factory('expr::lt_wjets_l_pt_correction_njets0_uncert%(i)i_up("((@0==0)*@1 + (@0!=0))*(@2>=%(crosstrg_pt)s) + (@2<%(crosstrg_pt)s)", njets[0], lt_wjets_l_pt_njets0_correction_uncert%(i)i_up, l_pt_bounded200)' % vars())
  w.factory('expr::lt_wjets_l_pt_correction_njets1_uncert%(i)i_up("((@0==0) + (@0!=0)*@1)*(@2>=%(crosstrg_pt)s) + (@2<%(crosstrg_pt)s)", njets[0], lt_wjets_l_pt_njets1_correction_uncert%(i)i_up, l_pt_bounded200)' % vars())

  w.factory('expr::lt_wjets_extrap_correction_uncert%(i)i_up("(@0>=70) + (@0<70&&@0>=50)*((@1==0)*@2 + (@1>0)*@3) + (@0<50)*((@1==0)*@4 + (@1>0)*@5) ",mt[0], nbjets[0], lt_wjets_extrap_nbjets0_loosemt_correction_uncert%(i)i_up, lt_wjets_extrap_nbjets1_loosemt_correction_uncert%(i)i_up, lt_wjets_extrap_nbjets0_tightmt_correction_uncert%(i)i_up, lt_wjets_extrap_nbjets1_tightmt_correction_uncert%(i)i_up)' % vars())

  w.factory('expr::lt_wjets_met_correction_njets0_uncert%(i)i_down("2.-@0", lt_wjets_met_correction_njets0_uncert%(i)i_up)' % vars())
  w.factory('expr::lt_wjets_met_correction_njets1_uncert%(i)i_down("2.-@0", lt_wjets_met_correction_njets1_uncert%(i)i_up)' % vars())
  w.factory('expr::lt_wjets_l_pt_correction_njets0_uncert%(i)i_down("2.-@0", lt_wjets_l_pt_correction_njets0_uncert%(i)i_up)' % vars())
  w.factory('expr::lt_wjets_l_pt_correction_njets1_uncert%(i)i_down("2.-@0", lt_wjets_l_pt_correction_njets1_uncert%(i)i_up)' % vars())
  w.factory('expr::lt_wjets_extrap_correction_uncert%(i)i_down("2.-@0", lt_wjets_extrap_correction_uncert%(i)i_up)' % vars())

# get final wjets fake factor
w.factory('expr::ff_lt_wjets("@0*@1*@2", ff_lt_wjets_raw, lt_wjets_dr_correction, lt_wjets_extrap_correction)' % vars())

wjets_systs=[]

# statistical uncertainties on measured wjets fake factors
# add statistical uncertainties 1 per njets/jetpt bin
for njet in [0,1]:
  for jetpt in jetpt_bins:
      short_name='%(jetpt)s_%(njet)ijet_wjets' % vars()
      for i in [1,2,3,4]:
        # possibly up to 4 uncerts per bin but in some cases uncert4 is a dummy
        w.factory('expr::ff_lt_wjets_stat_njet%(njet)i_%(jetpt)s_unc%(i)i_up("@0*@1",ff_lt_wjets, lt_%(short_name)s_uncert%(i)i_up)' % vars())
        w.factory('expr::ff_lt_wjets_stat_njet%(njet)i_%(jetpt)s_unc%(i)i_down("@0*@1",ff_lt_wjets, lt_%(short_name)s_uncert%(i)i_down)' % vars())
        wjets_systs.append('wjets_stat_njet%(njet)i_%(jetpt)s_unc%(i)i' % vars())

# systematic uncertainty from applying os/ss correction twice or not applying it 
w.factory('expr::ff_lt_wjets_syst_up("@0*@1*@2*@2", ff_lt_wjets_raw, lt_wjets_dr_correction, lt_wjets_extrap_correction)' % vars())
w.factory('expr::ff_lt_wjets_syst_down("@0*@1", ff_lt_wjets_raw, lt_wjets_dr_correction)' % vars())
wjets_systs.append('wjets_syst')

## statistical uncertainties on met, pt_1 and high->low mT extrap closure corrections
for i in [1,2]:
  w.factory('expr::ff_lt_wjets_stat_met_njets0_unc%(i)i_up("@0*@1", ff_lt_wjets, lt_wjets_met_correction_njets0_uncert%(i)i_up)' % vars())
  w.factory('expr::ff_lt_wjets_stat_met_njets0_unc%(i)i_down("@0*@1", ff_lt_wjets, lt_wjets_met_correction_njets0_uncert%(i)i_down)' % vars())
  w.factory('expr::ff_lt_wjets_stat_met_njets1_unc%(i)i_up("@0*@1", ff_lt_wjets, lt_wjets_met_correction_njets1_uncert%(i)i_up)' % vars())
  w.factory('expr::ff_lt_wjets_stat_met_njets1_unc%(i)i_down("@0*@1", ff_lt_wjets, lt_wjets_met_correction_njets1_uncert%(i)i_down)' % vars())

  wjets_systs.append('wjets_stat_met_njets0_unc%(i)i' % vars())
  wjets_systs.append('wjets_stat_met_njets1_unc%(i)i' % vars())

  w.factory('expr::ff_lt_wjets_stat_l_pt_njets0_unc%(i)i_up("@0*@1", ff_lt_wjets,   lt_wjets_l_pt_correction_njets0_uncert%(i)i_up)' % vars())
  w.factory('expr::ff_lt_wjets_stat_l_pt_njets0_unc%(i)i_down("@0*@1", ff_lt_wjets, lt_wjets_l_pt_correction_njets0_uncert%(i)i_down)' % vars())
  w.factory('expr::ff_lt_wjets_stat_l_pt_njets1_unc%(i)i_up("@0*@1", ff_lt_wjets,   lt_wjets_l_pt_correction_njets1_uncert%(i)i_up)' % vars())
  w.factory('expr::ff_lt_wjets_stat_l_pt_njets1_unc%(i)i_down("@0*@1", ff_lt_wjets, lt_wjets_l_pt_correction_njets1_uncert%(i)i_down)' % vars())

  wjets_systs.append('wjets_stat_l_pt_njets0_unc%(i)i' % vars())
  wjets_systs.append('wjets_stat_l_pt_njets1_unc%(i)i' % vars())

  w.factory('expr::ff_lt_wjets_stat_extrap_unc%(i)i_up("@0*@1", ff_lt_wjets,   lt_wjets_extrap_correction_uncert%(i)i_up)' % vars())
  w.factory('expr::ff_lt_wjets_stat_extrap_unc%(i)i_down("@0*@1", ff_lt_wjets, lt_wjets_extrap_correction_uncert%(i)i_down)' % vars())
  wjets_systs.append('wjets_stat_extrap_unc%(i)i' % vars())

print 'wjets systematics:'
print wjets_systs

#TODO: change high->low mT to pT correction, check if flat-only correction is better for nbjets>0 bins

# apply ttbar corrections

func_met_1 = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:met_tightmT_closure_ttbar_mc_fit' % vars())
func_met_str_1=str(func_met_1.GetExpFormula('p')).replace('x','@0').replace(',false','')

func_met_2 = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:met_loosemT_closure_ttbar_mc_fit' % vars())
func_met_str_2=str(func_met_2.GetExpFormula('p')).replace('x','@0').replace(',false','')

func_l_pt_1 = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:tightmT_closure_ttbar_mc_fit' % vars())
func_l_pt_str_1=str(func_l_pt_1.GetExpFormula('p')).replace('x','@0').replace(',false','')

func_l_pt_2 = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:loosemT_closure_ttbar_mc_fit' % vars())
func_l_pt_str_2=str(func_l_pt_2.GetExpFormula('p')).replace('x','@0').replace(',false','')

w.factory('expr::lt_ttbar_met_tightmt_correction("max(%(func_met_str_1)s,0.)",met_bounded)' % vars())
w.factory('expr::lt_ttbar_met_loosemt_correction("max(%(func_met_str_2)s,0.)",met_bounded)' % vars())
# note the l_pt ones are actually just for uncertainties
w.factory('expr::lt_ttbar_l_pt_tightmt_correction("max(%(func_l_pt_str_1)s,0.)",l_pt_bounded250)' % vars())
w.factory('expr::lt_ttbar_l_pt_loosemt_correction("max(%(func_l_pt_str_2)s,0.)",l_pt_bounded250)' % vars())

# get stat uncertainties

hist_met_nom_1 = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:met_tightmT_closure_ttbar_mc_fit' % vars())
hist_met_nom_2 = GetFromTFile(loc+'fakefactor_fits_%(channel)s_%(wp)s_%(year)s.root:met_loosemT_closure_ttbar_mc_fit' % vars())

(uncert1_up, uncert1_down, uncert2_up, uncert_2_down) = wsptools.SplitUncert(hist_met_nom_1)

wsptools.SafeWrapHist(w, ['met_bounded'], hist_met_nom_1, name='lt_ttbar_tightmt_met_correction_nom' % vars())
wsptools.SafeWrapHist(w, ['met_bounded'], uncert1_up,     name='lt_ttbar_tightmt_met_correction_uncert1_hist_up' % vars())
wsptools.SafeWrapHist(w, ['met_bounded'], uncert2_up,     name='lt_ttbar_tightmt_met_correction_uncert2_hist_up' % vars())

(uncert1_up, uncert1_down, uncert2_up, uncert_2_down) = wsptools.SplitUncert(hist_met_nom_2)

wsptools.SafeWrapHist(w, ['met_bounded'], hist_met_nom_2, name='lt_ttbar_loosemt_met_correction_nom' % vars())
wsptools.SafeWrapHist(w, ['met_bounded'], uncert1_up,     name='lt_ttbar_loosemt_met_correction_uncert1_hist_up' % vars())
wsptools.SafeWrapHist(w, ['met_bounded'], uncert2_up,     name='lt_ttbar_loosemt_met_correction_uncert2_hist_up' % vars())

w.factory('expr::lt_ttbar_met_tightmt_correction_uncert1_up("@0/@1", lt_ttbar_tightmt_met_correction_uncert1_hist_up, lt_ttbar_tightmt_met_correction_nom)' % vars())
w.factory('expr::lt_ttbar_met_tightmt_correction_uncert2_up("@0/@1", lt_ttbar_tightmt_met_correction_uncert2_hist_up, lt_ttbar_tightmt_met_correction_nom)' % vars())
w.factory('expr::lt_ttbar_met_loosemt_correction_uncert1_up("@0/@1", lt_ttbar_loosemt_met_correction_uncert1_hist_up, lt_ttbar_loosemt_met_correction_nom)' % vars())
w.factory('expr::lt_ttbar_met_loosemt_correction_uncert2_up("@0/@1", lt_ttbar_loosemt_met_correction_uncert2_hist_up, lt_ttbar_loosemt_met_correction_nom)' % vars())

w.factory('expr::lt_ttbar_met_correction("(@0<50)*@1 + (@0>=50)*@2",mt[0], lt_ttbar_met_tightmt_correction, lt_ttbar_met_loosemt_correction )' % vars())
w.factory('expr::lt_ttbar_l_pt_correction("(@0<50)*@1 + (@0>=50)*@2",mt[0], lt_ttbar_l_pt_tightmt_correction, lt_ttbar_l_pt_loosemt_correction )' % vars())

for i in [1,2]:
  w.factory('expr::lt_ttbar_met_correction_uncert%(i)i_up("(@0<50)*@1 + (@0>=50)*@2", mt[0], lt_ttbar_met_tightmt_correction_uncert%(i)i_up, lt_ttbar_met_loosemt_correction_uncert%(i)i_up)' % vars())
  w.factory('expr::lt_ttbar_met_correction_uncert%(i)i_down("2.-@0", lt_ttbar_met_correction_uncert%(i)i_up)' % vars())

#TODO: define lt_ttbar_datamc_correction 
w.factory('expr::lt_ttbar_datamc_correction("(@0>=0)*((@1<1.25*@2)*@3/@4 + (@1>=1.25*@2&&@1<1.5*@2)*@5/@6 + (@1>=1.5*@2)*@7/@8)", njets[0], jetpt[40], pt_bounded, lt_jet_pt_low_1jet_wjets_pt140_fit, lt_jet_pt_low_1jet_wjets_mc_pt140_fit, lt_jet_pt_medium_1jet_wjets_pt140_fit, lt_jet_pt_medium_1jet_wjets_mc_pt140_fit, lt_jet_pt_high_1jet_wjets_pt140_fit, lt_jet_pt_high_1jet_wjets_mc_pt140_fit)' % vars())

# get final qcd fake factor
w.factory('expr::ff_lt_ttbar("@0*@1*@2", ff_lt_ttbar_raw, lt_ttbar_met_correction, lt_ttbar_datamc_correction)' % vars())

ttbar_systs=[]

w.Print()
w.writeToFile('fakefactors_ws_%(channel)s_mssm_%(year)s.root' % vars())
w.Delete() 