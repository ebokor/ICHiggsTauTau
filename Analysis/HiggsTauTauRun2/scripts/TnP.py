import ROOT
import os
import glob
import json
from UserCode.ICHiggsTauTau.analysis import *
from UserCode.ICHiggsTauTau.uncertainties import ufloat
from optparse import OptionParser
import argparse
import ConfigParser
import UserCode.ICHiggsTauTau.plotting as plotting
from collections import OrderedDict
import copy
import sys
ROOT.RooWorkspace.imp = getattr(ROOT.RooWorkspace, 'import')
ROOT.TH1.AddDirectory(0)
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(ROOT.kTRUE)
ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)

CHANNELS= ['tpzmm','tpzee']

conf_parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    add_help=False
    )
conf_parser.add_argument("--cfg",
                    help="Specify config file", metavar="FILE")
options, remaining_argv = conf_parser.parse_known_args()

defaults = {
    "channel":"tpzmm" , 
    "outputfolder":"plots/TnP/embed/2018/tpzmm/",
    "folder":"/vols/cms/dw515/outputs/MSSM/UL_Mar31_2018_v2_TAP/",
    "era":"UL_18", 
    "draw_hists":1,
    "veto_FSR":False,
    "trg_only":False,
    "tree_name":"tagandprobe",
    "mode": "",
    "tight_tag":False,
    "embedded": False,
    "embed_sel": False,
    "embed_dz": False,
    }

if options.cfg:
    config = ConfigParser.SafeConfigParser()
    config.read([options.cfg])
    defaults.update(dict(config.items("Defaults")))

parser = argparse.ArgumentParser(
    parents=[conf_parser]
    )
parser.set_defaults(**defaults)
parser.add_argument("--channel", dest="channel", type=str,
    help="Tau decay channel to process.  Supported channels: %(CHANNELS)s" % vars())
parser.add_argument("--outputfolder", dest="outputfolder", type=str,
    help="Name of output folder")
parser.add_argument("--folder", dest="folder", type=str,
    help="Name of input folder")
parser.add_argument("--era", dest="era", type=str,
    help="Era")
parser.add_argument("--draw_hists", dest="draw_hists", type=int,
    help="If set to 0 then will not re-make the 3D histograms instead will use the histograms on the existing root file")
parser.add_argument("--veto_FSR", dest='veto_FSR', action='store_true', 
    help="If true, the events with FSR are vetoed (only applied to isolation)")
parser.add_argument("--trg_only", dest='trg_only', action='store_true',
    help="If true only the trigger SFs are computed")
parser.add_argument("--tree_name", dest="tree_name", type=str,
    help="If set then uses a custom name for the input tree used to produce the SFs. If not set this will be tagandprobe by default")
parser.add_argument("--mode", dest="mode",type=str)
parser.add_argument("--tight_tag", dest="tight_tag", action='store_true')
parser.add_argument("--embedded", dest="embedded", action='store_true')
parser.add_argument("--embed_sel", dest="embed_sel", action='store_true')
parser.add_argument("--embed_dz", dest="embed_dz", action='store_true')


options = parser.parse_args(remaining_argv)   

print ''
print '################### Options ###################'
print 'channel           = ' + options.channel
print 'outputfolder      = ' + options.outputfolder
print 'folder            = ' + options.folder
print 'era               = ' + options.era
print 'draw_hists        =', options.draw_hists
print 'veto_FSR          =', options.veto_FSR
print 'tree              =', options.tree_name
print 'mode              =', options.mode
print 'tight tag         =', options.tight_tag
print 'embedded          =', options.embedded
print 'embed sel         =', options.embed_sel
print 'embed dz          =', options.embed_dz
print '###############################################'
print ''

# All functions defined here

def BuildCutString(wt='', sel='', cat='', sign='os',bkg_sel=''):
    full_selection = '(1)'
    if wt != '':          
        full_selection = '('+wt+')'
    if sel != '':
        full_selection += '*('+sel+')'
    if sign != '':
        full_selection += '*('+sign+')'
    if bkg_sel != '':
        full_selection += '*('+bkg_sel+')'
    if cat != '':
        full_selection += '*('+cat+')'
    return full_selection

def GetZLLNode(ana, add_name='', samples=[], plot='', wt='', sel='', cat=''):
    full_selection = BuildCutString(wt, sel, cat, '1', '1')

    return ana.SummedFactory('ZLL'+add_name, samples, plot, full_selection)

def GetDataNode(ana, add_name='', samples=[], plot='', wt='', sel='', cat=''):
    full_selection = BuildCutString('', sel, cat, '1', '1')
    return ana.SummedFactory('data'+add_name, samples, plot, full_selection)

def GetEmbeddedNode(ana, add_name='', samples=[], plot='', wt='', sel='', cat=''):
    full_selection = BuildCutString('', sel, cat, '1', '1')
    return ana.SummedFactory('EmbedZLL'+add_name, samples, plot, full_selection)

def GenerateZLL(ana, add_name='', samples=[], plot='', wt='', sel='', cat=''):
    zll_node = GetZLLNode(ana, add_name, samples, plot, wt, sel, cat)
    ana.nodes[nodename].AddNode(zll_node)

def GenerateData(ana, add_name='', samples=[], plot='', wt='', sel='', cat=''):
    data_node = GetDataNode(ana, add_name, samples, plot, wt, sel, cat)
    ana.nodes[nodename].AddNode(data_node)

def GenerateEmbedded(ana, add_name='', samples=[], plot='', wt='', sel='', cat=''):
    embed_node = GetEmbeddedNode(ana, add_name, samples, plot, wt, sel, cat)
    ana.nodes[nodename].AddNode(embed_node)

def Produce3DHistograms(ana, wt='wt', outfile=None):
    if options.embed_sel or options.embed_dz: mass_bins = '(50,70,120)'
    #else: mass_bins = '(50,65,115)'
    mass_bins = '(50,70,120)'
    if options.channel == 'tpzmm':
      gen_cuts='gen_match_1==2&&gen_match_2==2'
      idiso_eta_bins = '[0,0.9,1.2,2.1,2.4]'
      idiso_pt_bins = '[10,15,20,25,30,40,45,50,55,60,70,80,100,200]'
      trg_eta_bins = '[0,0.9,1.2,2.1,2.4]'
      trg_pt_bins = '[15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,35,40,50,60,80,100,200]'
      iso_pt_bins = '[10,15,20,25,30,35,40,45,50,55,60,70,80,100,200]'
      if options.embed_sel:
        trg_eta_bins   = '[0,0.1,0.3,0.8,1.0,1.2,1.6,1.8,2.1,2.4]' #mu8
        idiso_eta_bins = '[0,0.1,0.3,0.8,1.0,1.2,1.6,1.8,2.1,2.4]' #mu8
        trg_pt_bins = '[10,12,14,15,17,19,21,22,23,24,25,26,27,28,31,34,37,40,45,50,60,70,100,1000]' # mu17
      if options.embed_dz:
        trg_eta_bins='[0,2.4]'
        trg_pt_bins='[28,1000]'


    if options.channel == 'tpzee':
      gen_cuts='gen_match_1==1&&gen_match_2==1'  
      #idiso_eta_bins = '[0, 1.0, 1.479, 1.653, 2.1, 2.5]'
      idiso_eta_bins = '[0, 0.8,1.444,1.566,2.0,2.5]'

      iso_pt_bins   = '[10,15,20,25,30,35,40,45,50,55,60,70,80,100,200]' 
      idiso_pt_bins = '[10,15,20,25,30,35,40,50,100,200]'

      trg_eta_bins = '[0, 0.8, 1.444, 1.566, 2.0, 2.5]'
      #trg_pt_bins = '[27,32,35,40,45,50,55,60,70,80,100,200]'
      trg_pt_bins = '[20,24,26,28,33,36,40,44,48,50,55,60,70,80,100,200]'


          
    trg_plot_probe_1 = 'abs(eta_1),pt_1,m_vis'+trg_eta_bins+','+trg_pt_bins+','+mass_bins
    trg_plot_probe_2 = 'abs(eta_2),pt_2,m_vis'+trg_eta_bins+','+trg_pt_bins+','+mass_bins
    idiso_plot_probe_1 = 'abs(eta_1),pt_1,m_vis'+idiso_eta_bins+','+idiso_pt_bins+','+mass_bins
    idiso_plot_probe_2 = 'abs(eta_2),pt_2,m_vis'+idiso_eta_bins+','+idiso_pt_bins+','+mass_bins
    iso_plot_probe_1 = 'abs(eta_1),pt_1,m_vis'+idiso_eta_bins+','+iso_pt_bins+','+mass_bins
    iso_plot_probe_2 = 'abs(eta_2),pt_2,m_vis'+idiso_eta_bins+','+iso_pt_bins+','+mass_bins

    if not options.embed_sel:
      GenerateZLL(ana, '_trg_tag1_fail', ztt_samples, trg_plot_probe_2, wt, trg_tag_1+'&&'+gen_cuts, '!%s' % trg_probe_2)
      GenerateZLL(ana, '_trg_tag2_fail', ztt_samples, trg_plot_probe_1, wt, trg_tag_2+'&&'+gen_cuts, '!%s' % trg_probe_1)
      GenerateZLL(ana, '_trg_tag1_pass', ztt_samples, trg_plot_probe_2, wt, trg_tag_1+'&&'+gen_cuts, trg_probe_2)
      GenerateZLL(ana, '_trg_tag2_pass', ztt_samples, trg_plot_probe_1, wt, trg_tag_2+'&&'+gen_cuts, trg_probe_1)    
    GenerateData(ana, '_trg_tag1_fail', data_samples, trg_plot_probe_2, wt, trg_tag_1, '!%s' % trg_probe_2)
    GenerateData(ana, '_trg_tag2_fail', data_samples, trg_plot_probe_1, wt, trg_tag_2, '!%s' % trg_probe_1)
    GenerateData(ana, '_trg_tag1_pass', data_samples, trg_plot_probe_2, wt, trg_tag_1, trg_probe_2)
    GenerateData(ana, '_trg_tag2_pass', data_samples, trg_plot_probe_1, wt, trg_tag_2, trg_probe_1)
   

    if not options.trg_only: 
      if not options.embed_sel:
        GenerateZLL(ana, '_id_tag1_fail', ztt_samples, idiso_plot_probe_2, wt, id_tag_1+'&&'+gen_cuts, '!%s' % id_probe_2)
        GenerateZLL(ana, '_id_tag2_fail', ztt_samples, idiso_plot_probe_1, wt, id_tag_2+'&&'+gen_cuts, '!%s' % id_probe_1)
        GenerateZLL(ana, '_id_tag1_pass', ztt_samples, idiso_plot_probe_2, wt, id_tag_1+'&&'+gen_cuts, id_probe_2)
        GenerateZLL(ana, '_id_tag2_pass', ztt_samples, idiso_plot_probe_1, wt, id_tag_2+'&&'+gen_cuts, id_probe_1)    
      GenerateData(ana, '_id_tag1_fail', data_samples, idiso_plot_probe_2, wt, id_tag_1, '!%s' % id_probe_2)
      GenerateData(ana, '_id_tag2_fail', data_samples, idiso_plot_probe_1, wt, id_tag_2, '!%s' % id_probe_1)
      GenerateData(ana, '_id_tag1_pass', data_samples, idiso_plot_probe_2, wt, id_tag_1, id_probe_2)
      GenerateData(ana, '_id_tag2_pass', data_samples, idiso_plot_probe_1, wt, id_tag_2, id_probe_1)

      if not options.embed_sel:
        GenerateZLL(ana, '_iso_tag1_fail', ztt_samples, iso_plot_probe_2, wt, iso_tag_1+'&&'+gen_cuts, '!%s' % iso_probe_2)
        GenerateZLL(ana, '_iso_tag2_fail', ztt_samples, iso_plot_probe_1, wt, iso_tag_2+'&&'+gen_cuts, '!%s' % iso_probe_1)
        GenerateZLL(ana, '_iso_tag1_pass', ztt_samples, iso_plot_probe_2, wt, iso_tag_1+'&&'+gen_cuts, iso_probe_2)
        GenerateZLL(ana, '_iso_tag2_pass', ztt_samples, iso_plot_probe_1, wt, iso_tag_2+'&&'+gen_cuts, iso_probe_1)   
        GenerateData(ana, '_iso_tag1_fail', data_samples, iso_plot_probe_2, wt, iso_tag_1, '!%s' % iso_probe_2)
        GenerateData(ana, '_iso_tag2_fail', data_samples, iso_plot_probe_1, wt, iso_tag_2, '!%s' % iso_probe_1)
        GenerateData(ana, '_iso_tag1_pass', data_samples, iso_plot_probe_2, wt, iso_tag_1, iso_probe_2)
        GenerateData(ana, '_iso_tag2_pass', data_samples, iso_plot_probe_1, wt, iso_tag_2, iso_probe_1)

    if options.embedded and not (options.embed_sel or options.embed_dz):
       
      GenerateEmbedded(ana, '_trg_tag1_fail', embed_samples, trg_plot_probe_2, wt, trg_tag_1+'&&'+gen_cuts, '!%s' % trg_probe_2)
      GenerateEmbedded(ana, '_trg_tag2_fail', embed_samples, trg_plot_probe_1, wt, trg_tag_2+'&&'+gen_cuts, '!%s' % trg_probe_1)
      GenerateEmbedded(ana, '_trg_tag1_pass', embed_samples, trg_plot_probe_2, wt, trg_tag_1+'&&'+gen_cuts, trg_probe_2)
      GenerateEmbedded(ana, '_trg_tag2_pass', embed_samples, trg_plot_probe_1, wt, trg_tag_2+'&&'+gen_cuts, trg_probe_1)
   
      if not options.trg_only:      
        GenerateEmbedded(ana, '_id_tag1_fail', embed_samples, idiso_plot_probe_2, wt, id_tag_1+'&&'+gen_cuts, '!%s' % id_probe_2)
        GenerateEmbedded(ana, '_id_tag2_fail', embed_samples, idiso_plot_probe_1, wt, id_tag_2+'&&'+gen_cuts, '!%s' % id_probe_1)
        GenerateEmbedded(ana, '_id_tag1_pass', embed_samples, idiso_plot_probe_2, wt, id_tag_1+'&&'+gen_cuts, id_probe_2)
        GenerateEmbedded(ana, '_id_tag2_pass', embed_samples, idiso_plot_probe_1, wt, id_tag_2+'&&'+gen_cuts, id_probe_1)
         
        GenerateEmbedded(ana, '_iso_tag1_fail', embed_samples, iso_plot_probe_2, wt, fix_iso_tag_1+'&&'+gen_cuts, '!%s' % iso_probe_2)
        GenerateEmbedded(ana, '_iso_tag2_fail', embed_samples, iso_plot_probe_1, wt, fix_iso_tag_2+'&&'+gen_cuts, '!%s' % iso_probe_1)
        GenerateEmbedded(ana, '_iso_tag1_pass', embed_samples, iso_plot_probe_2, wt, fix_iso_tag_1+'&&'+gen_cuts, iso_probe_2)
        GenerateEmbedded(ana, '_iso_tag2_pass', embed_samples, iso_plot_probe_1, wt, fix_iso_tag_2+'&&'+gen_cuts, iso_probe_1)
    
    

    ana.Run()
    ana.nodes.Output(outfile)
    
    outfile.cd()
    
    if not options.embed_sel: 
      zll_trg_fail = outfile.Get(nodename+'/ZLL_trg_tag1_fail').Clone()
      zll_trg_fail.Add(outfile.Get(nodename+'/ZLL_trg_tag2_fail'))
      zll_trg_pass = outfile.Get(nodename+'/ZLL_trg_tag1_pass').Clone()
      zll_trg_pass.Add(outfile.Get(nodename+'/ZLL_trg_tag2_pass'))
      zll_trg_fail.SetName('ZLL_trg_fail')
      zll_trg_pass.SetName('ZLL_trg_pass')
      zll_trg_fail.Write('ZLL_trg_fail')
      zll_trg_pass.Write('ZLL_trg_pass')
    
    data_trg_fail = outfile.Get(nodename+'/data_trg_tag1_fail').Clone()
    data_trg_fail.Add(outfile.Get(nodename+'/data_trg_tag2_fail'))
    data_trg_pass = outfile.Get(nodename+'/data_trg_tag1_pass').Clone()
    data_trg_pass.Add(outfile.Get(nodename+'/data_trg_tag2_pass'))
    data_trg_fail.SetName('data_trg_fail')
    data_trg_pass.SetName('data_trg_pass')
    data_trg_fail.Write('data_trg_fail')
    data_trg_pass.Write('data_trg_pass')

    if not options.trg_only:    
      if not options.embed_sel:
        zll_id_fail = outfile.Get(nodename+'/ZLL_id_tag1_fail').Clone()
        zll_id_fail.Add(outfile.Get(nodename+'/ZLL_id_tag2_fail'))
        zll_id_pass = outfile.Get(nodename+'/ZLL_id_tag1_pass').Clone()
        zll_id_pass.Add(outfile.Get(nodename+'/ZLL_id_tag2_pass'))
        zll_id_fail.SetName('ZLL_id_fail')
        zll_id_pass.SetName('ZLL_id_pass')
        zll_id_fail.Write('ZLL_id_fail')
        zll_id_pass.Write('ZLL_id_pass')
      
      data_id_fail = outfile.Get(nodename+'/data_id_tag1_fail').Clone()
      data_id_fail.Add(outfile.Get(nodename+'/data_id_tag2_fail'))
      data_id_pass = outfile.Get(nodename+'/data_id_tag1_pass').Clone()
      data_id_pass.Add(outfile.Get(nodename+'/data_id_tag2_pass'))
      data_id_fail.SetName('data_id_fail')
      data_id_pass.SetName('data_id_pass')
      data_id_fail.Write('data_id_fail')
      data_id_pass.Write('data_id_pass')
      
      if not options.embed_sel:
        zll_iso_fail = outfile.Get(nodename+'/ZLL_iso_tag1_fail').Clone()
        zll_iso_fail.Add(outfile.Get(nodename+'/ZLL_iso_tag2_fail'))
        zll_iso_pass = outfile.Get(nodename+'/ZLL_iso_tag1_pass').Clone()
        zll_iso_pass.Add(outfile.Get(nodename+'/ZLL_iso_tag2_pass'))
        zll_iso_fail.SetName('ZLL_iso_fail')
        zll_iso_pass.SetName('ZLL_iso_pass')
        zll_iso_fail.Write('ZLL_iso_fail')
        zll_iso_pass.Write('ZLL_iso_pass')
      
        data_iso_fail = outfile.Get(nodename+'/data_iso_tag1_fail').Clone()
        data_iso_fail.Add(outfile.Get(nodename+'/data_iso_tag2_fail'))
        data_iso_pass = outfile.Get(nodename+'/data_iso_tag1_pass').Clone()
        data_iso_pass.Add(outfile.Get(nodename+'/data_iso_tag2_pass'))
        data_iso_fail.SetName('data_iso_fail')
        data_iso_pass.SetName('data_iso_pass')
        data_iso_fail.Write('data_iso_fail')
        data_iso_pass.Write('data_iso_pass')

    if options.embedded:
      
      embed_trg_fail = outfile.Get(nodename+'/EmbedZLL_trg_tag1_fail').Clone()
      embed_trg_fail.Add(outfile.Get(nodename+'/EmbedZLL_trg_tag2_fail'))
      embed_trg_pass = outfile.Get(nodename+'/EmbedZLL_trg_tag1_pass').Clone()
      embed_trg_pass.Add(outfile.Get(nodename+'/EmbedZLL_trg_tag2_pass'))
      embed_trg_fail.SetName('embed_trg_fail')
      embed_trg_pass.SetName('embed_trg_pass')
      embed_trg_fail.Write('embed_trg_fail')
      embed_trg_pass.Write('embed_trg_pass')
     
      if not options.trg_only:
 
        embed_id_fail = outfile.Get(nodename+'/EmbedZLL_id_tag1_fail').Clone()
        embed_id_fail.Add(outfile.Get(nodename+'/EmbedZLL_id_tag2_fail'))
        embed_id_pass = outfile.Get(nodename+'/EmbedZLL_id_tag1_pass').Clone()
        embed_id_pass.Add(outfile.Get(nodename+'/EmbedZLL_id_tag2_pass'))
        embed_id_fail.SetName('embed_id_fail')
        embed_id_pass.SetName('embed_id_pass')
        embed_id_fail.Write('embed_id_fail')
        embed_id_pass.Write('embed_id_pass')
        
        embed_iso_fail = outfile.Get(nodename+'/EmbedZLL_iso_tag1_fail').Clone()
        embed_iso_fail.Add(outfile.Get(nodename+'/EmbedZLL_iso_tag2_fail'))
        embed_iso_pass = outfile.Get(nodename+'/EmbedZLL_iso_tag1_pass').Clone()
        embed_iso_pass.Add(outfile.Get(nodename+'/EmbedZLL_iso_tag2_pass'))
        embed_iso_fail.SetName('embed_iso_fail')
        embed_iso_pass.SetName('embed_iso_pass')
        embed_iso_fail.Write('embed_iso_fail')
        embed_iso_pass.Write('embed_iso_pass')

    
def Get1DHistsFrom3D(passhist3d,failhist3d):
  # z = eta, y = pt, x = mass
  hists = []
  for j in range(1,passhist3d.GetNbinsY()+1):
      for k in range(1,passhist3d.GetNbinsZ()+1):
        ymin = passhist3d.GetYaxis().GetBinLowEdge(j)    
        ymax = passhist3d.GetYaxis().GetBinUpEdge(j)
        zmin = passhist3d.GetZaxis().GetBinLowEdge(k)
        zmax = passhist3d.GetZaxis().GetBinUpEdge(k)
        passname1d = '%s_pt_%.0f_to_%.0f_eta_%.1f_to_%.1f' % (passhist3d.GetName(),ymin,ymax,zmin,zmax)
        failname1d = '%s_pt_%.0f_to_%.0f_eta_%.1f_to_%.1f' % (failhist3d.GetName(),ymin,ymax,zmin,zmax)
        passhist1d = passhist3d.ProjectionX(passname1d,j,j,k,k)
        failhist1d = failhist3d.ProjectionX(failname1d,j,j,k,k)
        hists.append((passhist1d,failhist1d,ymin,ymax,zmin,zmax))
  return hists
      
def CreateWorkspace(name,infile,outfile):
  wsp = ROOT.RooWorkspace('wsp_'+name, '')
  hists = Get1DHistsFrom3D(infile.Get('%s_pass' % name),infile.Get('%s_fail' % name))  
  hist2d = infile.Get('%s_pass' % name).Project3D("zy")
  hist2d.Reset()
  hist2d.SetName('%s_eff' % name)
  hist2d.SetTitle('')
  hist2d.GetXaxis().SetTitle('pt')
  hist2d.GetYaxis().SetTitle('eta')
  wsp = ROOT.RooWorkspace('wsp_'+name, '')
  var = wsp.factory('m_vis[100,50,150]')    
  
  outfile.cd()
  outfile.mkdir(name)
  ROOT.gDirectory.cd(name)
  
  for hist in hists:
    hist[0].Write()
    hist[1].Write()
    dat = wsp.imp(ROOT.RooDataHist(hist[0].GetName().replace('_pass',''), '', ROOT.RooArgList(var),
                  ROOT.RooFit.Index(wsp.factory('cat[fail,pass]')),
                  ROOT.RooFit.Import('fail', hist[1]),
                  ROOT.RooFit.Import('pass', hist[0])))
  
  wsp.Write()
  hist2d.Write()
  wsp.Delete()
  
def FitWorkspace(name,infile,outfile,sig_model='DoubleVCorr',bkg_model='Exponential',scenario="nominal",doFit=True):
  wsp = infile.Get(name+'/wsp_'+name)
  pdf_args = [ ]
  nparams = 1

  if sig_model == 'DoubleVCorr':
    nparams = 6
    pdf_args.extend(
            [
                "Voigtian::signal1Pass(m_vis, mean1[90,85,95], width[2.495], sigma1[2,0.2,4])",
                "Voigtian::signal2Pass(m_vis, mean2[90,85,95], width,        sigma2[4,2,10])",
                "SUM::signalPass(vFrac[0.8,0,1]*signal1Pass, signal2Pass)",
                "Voigtian::signal1Fail(m_vis, mean1[90,85,95], width[2.495], sigma1[2,0.2,4])",
                "Voigtian::signal2Fail(m_vis, mean2[90,85,95], width,        sigma2[4,2,10])",
                "SUM::signalFail(vFrac[0.8,0,1]*signal1Fail, signal2Fail)",
            ]
        )
  elif sig_model == 'DoubleVUncorr':
      nparams = 6
      pdf_args.extend(
              [
                  "Voigtian::signal1Pass(m_vis, mean1p[90,85,95], widthp[2.495], sigma1p[2,0.2,4])",
                  "Voigtian::signal2Pass(m_vis, mean2p[90,85,95], widthp,        sigma2p[4,2,10])",
                  "SUM::signalPass(vFracp[0.8,0,1]*signal1Pass, signal2Pass)",
                  "Voigtian::signal1Fail(m_vis, mean1f[90,85,95], widthf[2.495], sigma1f[2,0.2,4])",
                  "Voigtian::signal2Fail(m_vis, mean2f[90,85,95], widthf,        sigma2f[4,2,10])",
                  "SUM::signalFail(vFracf[0.8,0,1]*signal1Fail, signal2Fail)"
              ]
          )
  elif sig_model == 'DoubleVUncorr_18':
      nparams = 6
      pdf_args.extend(
              [
                  "Voigtian::signal1Pass(m_vis, mean1p[90,85,95], widthp[2.495], sigma1p[2,1,4])",
                  "Voigtian::signal2Pass(m_vis, mean2p[90,85,95], widthp,        sigma2p[4,2,10])",
                  "SUM::signalPass(vFracp[0.8,0,1]*signal1Pass, signal2Pass)",
                  "Voigtian::signal1Fail(m_vis, mean1f[90,85,95], widthf[2.495], sigma1f[2,1,4])",
                  "Voigtian::signal2Fail(m_vis, mean2f[90,85,95], widthf,        sigma2f[4,2,10])",
                  "SUM::signalFail(vFracf[0.8,0,1]*signal1Fail, signal2Fail)"
              ]
          )
  elif sig_model == 'DoubleVUncorr_elec':
      nparams = 6
      pdf_args.extend(
              [
                  "Voigtian::signal1Pass(m_vis, mean1p[90,85,95], widthp[2.495], sigma1p[2,0.2,4])",
                  "Voigtian::signal2Pass(m_vis, mean2p[90,85,95], widthp,        sigma2p[4,0.5,10])",
                  "SUM::signalPass(vFracp[0.8,0,1]*signal1Pass, signal2Pass)",
                  "Voigtian::signal1Fail(m_vis, mean1f[90,85,95], widthf[2.495], sigma1f[2,0.2,4])",
                  "Voigtian::signal2Fail(m_vis, mean2f[90,85,95], widthf,        sigma2f[4,0.5,10])",
                  "SUM::signalFail(vFracf[0.8,0,1]*signal1Fail, signal2Fail)"

              ]
          )
  elif sig_model == 'DoubleVUncorr_elec_18':
      pdf_args.extend(
              [
                  "Voigtian::signal1Pass(m_vis, mean1p[90,87,92], widthp[2.495], sigma1p[2,0.2,4])",
                  "expr::sigma2p('sigma1p+x', sigma1p, x[0,0,2])",
                  "Voigtian::signal2Pass(m_vis, mean2p[90,85,95], widthp,        sigma2p)",
                  "SUM::signalPass(vFracp[0.8,0,1]*signal1Pass, signal2Pass)",
                  "Voigtian::signal1Fail(m_vis, mean1f[90,87,92], widthf[2.495], sigma1f[2,0.2,4])",
                  "expr::sigma2f('sigma1f+y', sigma1f, y[0,0,2])",
                  "Voigtian::signal2Fail(m_vis, mean2f[90,85,95], widthf,        sigma2f)",
                  "SUM::signalFail(vFracf[0.8,0,1]*signal1Fail, signal2Fail)"

              ]
          )
  elif sig_model == 'DoubleVUncorr_elec_TwoPeaks':
      nparams = 6
      pdf_args.extend(
              [
                  "Voigtian::signal1Pass(m_vis, mean1p[90,85,95], widthp[2.495], sigma1p[2,0.2,4])",
                  "Voigtian::signal2Pass(m_vis, mean2p[90,85,95], widthp,        sigma2p[4,0.5,10])",
                  "SUM::signalPass(vFracp[0.8,0,1]*signal1Pass, signal2Pass)",
                  "Voigtian::signal1Fail(m_vis, mean1f[90,85,95], widthf[2.495], sigma1f[2,0.2,4])",
                  "Voigtian::signal2Fail(m_vis, mean2f[90,70,95], widthf,        sigma2f[4,0.5,10])",
                  "SUM::signalFail(vFracf[0.8,0,1]*signal1Fail, signal2Fail)"

              ]
          )


  elif sig_model == 'DoubleVPartcorr':
      nparams = 6
      pdf_args.extend(
              [
                  "Voigtian::signal1Pass(m_vis, mean[90,85,95], width[2.495], sigma[2,0.2,4])",
                  "Voigtian::signal2Pass(m_vis, meanp[90,85,95], width[2.495], sigmap[2,1,10])",
                  "SUM::signalPass(vFracp[0.01,0,1]*signal1Pass, signal2Pass)",
                  "Voigtian::signal1Fail(m_vis, mean[90,85,95], width[2.495], sigma[2,0.2,4])",
                  "Voigtian::signal2Fail(m_vis, meanf[90,85,95], width[2.495], sigmaf[2,1,10])",
                  "SUM::signalFail(vFracf[0.01,0,1]*signal1Fail, signal2Fail)"
              ]
          )
  elif sig_model == 'DoubleVPartcorr_18':
      nparams = 6
      pdf_args.extend(
              [
                  "Voigtian::signal1Pass(m_vis, mean[90,85,95], width[2.495], sigma[2,1,4])",
                  "Voigtian::signal2Pass(m_vis, meanp[90,85,95], width[2.495], sigmap[2,1,15])",
                  "SUM::signalPass(vFracp[0.01,0,1]*signal1Pass, signal2Pass)",
                  "Voigtian::signal1Fail(m_vis, mean[90,85,95], width[2.495], sigma[2,1,4])",
                  "Voigtian::signal2Fail(m_vis, meanf[90,85,95], width[2.495], sigmaf[2,1,15])",
                  "SUM::signalFail(vFracf[0.01,0,1]*signal1Fail, signal2Fail)"
              ]
          )

  elif sig_model == 'DoubleVPartcorr_elec':
      nparams = 6
      pdf_args.extend(
              [
                  "Voigtian::signal1Pass(m_vis, mean[90,85,95], width[2.495], sigma[2,0.5,4])",
                  "Voigtian::signal2Pass(m_vis, meanp[90,85,95], width[2.495], sigmap[2,1,15])",
                  "SUM::signalPass(vFracp[0.01,0,1]*signal1Pass, signal2Pass)",
                  "Voigtian::signal1Fail(m_vis, mean[90,85,95], width[2.495], sigma[2,0.5,4])",
                  "Voigtian::signal2Fail(m_vis, meanf[90,85,95], width[2.495], sigmaf[2,1,15])",
                  "SUM::signalFail(vFracf[0.01,0,1]*signal1Fail, signal2Fail)"
              ]
          )

  elif sig_model == 'DoubleVPartcorr_TwoPeaks':
      nparams = 6
      pdf_args.extend(
              [
                  "Voigtian::signal1Pass(m_vis, mean[90,85,95], width[2.495], sigma[2,1,4])",
                  "Voigtian::signal2Pass(m_vis, meanp[90,85,95], width[2.495], sigmap[2,1,10])",
                  "SUM::signalPass(vFracp[0.01,0,1]*signal1Pass, signal2Pass)",
                  "Voigtian::signal1Fail(m_vis, mean[90,85,95], width[2.495], sigma[2,1,4])",
                  "Voigtian::signal2Fail(m_vis, meanf[90,70,100], width[2.495], sigmaf[2,1,15])",
                  "SUM::signalFail(vFracf[0.01,0,1]*signal1Fail, signal2Fail)"
              ]
          )
  elif sig_model == 'DoubleVPartcorr_TwoPeaks_18':
      nparams = 6
      pdf_args.extend(
              [
                  "Voigtian::signal1Pass(m_vis, mean[90,85,95], width[2.495], sigma[2,1,4])",
                  "Voigtian::signal2Pass(m_vis, meanp[90,80,100], width[2.495], sigmap[2,1,15])",
                  "SUM::signalPass(vFracp[0.01,0,1]*signal1Pass, signal2Pass)",
                  "Voigtian::signal1Fail(m_vis, mean[90,85,95], width[2.495], sigma[2,1,4])",
                  "Voigtian::signal2Fail(m_vis, meanf[90,70,100], width[2.495], sigmaf[2,1,15])",
                  "SUM::signalFail(vFracf[0.01,0,1]*signal1Fail, signal2Fail)"
              ]
          )

              
  elif sig_model == 'BWCBConvUncorr':
      nparams = 9
      pdf_args.extend(
              [
                  "BreitWigner::BW(m_vis, meanbw[0], widthbw[2.495])",
                  "CBShape::CBPass(m_vis, meanp[90,85,95], sigmap[2,1,10], alphap[1,0,50], np[1,0,50])",
                  "FFTConvPdf::signalPass(m_vis,CBPass,BW)",
                  "CBShape::CBFail(m_vis, meanf[90,85,95], sigmaf[2,1,10], alphaf[1,0,50], nf[1,0,50])",
                  "FFTConvPdf::signalFail(m_vis,CBFail,BW)",
              ]
          ) 
  elif sig_model == 'BWCBConvCorr':
      nparams = 5
      pdf_args.extend(
              [
                  "BreitWigner::BW(m_vis, meanbw[0], widthbw[2.495])",
                  "CBShape::CBPass(m_vis, mean[90,85,95], sigma[2,0.5,10], alpha[1,0,50], n[1,0,50])",
                  "FFTConvPdf::signalPass(m_vis,CBPass,BW)",
                  "CBShape::CBFail(m_vis, mean[90,85,95], sigma[2,0.5,10], alpha[1,0,50], n[1,0,50])",
                  "FFTConvPdf::signalFail(m_vis,CBFail,BW)",
              ]
          )            
  elif sig_model == 'BWDoubleCBConvUncorr':
      nparams = 19
      pdf_args.extend(
              [
                  "BreitWigner::BW(m_vis, meanbw[0], widthbw[2.495])",
                  "CBShape::CBPass1(m_vis, meanp1[90,80,100], sigmap1[2,0,10], alphap1[1,-50,50], np1[1,0,50])",
                  "CBShape::CBPass2(m_vis, meanp2[90,80,100], sigmap2[2,0,10], alphap2[1,-50,50], np2[1,0,50])",
                  "SUM::DoubleCBPass(CBPass1, vFracp[0.8,0,1]*CBPass2)",
                  "FFTConvPdf::signalPass(m_vis,DoubleCBPass,BW)",
                  "CBShape::CBFail1(m_vis, meanf1[90,80,100], sigmaf1[2,0,10], alphaf1[1,-50,50], nf1[1,0,50])",
                  "CBShape::CBFail2(m_vis, meanf2[90,80,100], sigmaf2[2,0,10], alphaf2[1,-50,50], nf2[1,0,50])",
                  "SUM::DoubleCBFail(CBFail1, vFracf[0.8,0,1]*CBFail2)",
                  "FFTConvPdf::signalFail(m_vis,DoubleCBFail,BW)",
              ]
          )          
  elif sig_model == 'BWDoubleCBConvUncorr_elec':
      nparams = 19
      pdf_args.extend(
              [
                  "BreitWigner::BW(m_vis, meanbw[0], widthbw[2.495])",
                  "CBShape::CBPass1(m_vis, meanp1[90,85,95], sigmap1[2,0.5,4], alphap1[1,0,50], np1[1,0,50])",
                  "CBShape::CBPass2(m_vis, meanp2[90,85,95], sigmap2[2,2,10], alphap2[1,0,50], np2[1,0,50])",
                  "SUM::DoubleCBPass(CBPass1, vFracp[0.8,0,1]*CBPass2)",
                  "FFTConvPdf::signalPass(m_vis,DoubleCBPass,BW)",
                  "CBShape::CBFail1(m_vis, meanf1[90,85,95], sigmaf1[2,0.5,4], alphaf1[1,0,50], nf1[1,0,50])",
                  "CBShape::CBFail2(m_vis, meanf2[90,85,95], sigmaf2[2,2,10], alphaf2[1,0,50], nf2[1,0,50])",
                  "SUM::DoubleCBFail(CBFail1, vFracf[0.8,0,1]*CBFail2)",
                  "FFTConvPdf::signalFail(m_vis,DoubleCBFail,BW)",
              ]
          )
 
  elif sig_model == 'BWDoubleCBConvCorr':
      nparams = 15
      pdf_args.extend(
              [
                  "BreitWigner::BW(m_vis, meanbw[0], widthbw[2.495])",
                  "CBShape::CBPass1(m_vis, mean[90,80,100], sigma[2,1,4], alpha[1,-50,50], n[1,0,50])",
                  "CBShape::CBPass2(m_vis, meanp[90,80,100], sigmap[4,4,10], alphap[1,-50,50], np[1,0,50])",
                  "SUM::DoubleCBPass(CBPass1, vFracp[0.01,0,1]*CBPass2)",
                  "FFTConvPdf::signalPass(m_vis,DoubleCBPass,BW)",
                  "CBShape::CBFail1(m_vis, mean[90,80,100], sigma[2,1,4], alpha[1,-50,50], n[1,0,50])",
                  "CBShape::CBFail2(m_vis, meanf[90,80,100], sigmaf[4,4,10], alphaf[1,-50,50], nf[1,0,50])",
                  "SUM::DoubleCBFail(CBFail1, vFracf[0.01,0,1]*CBFail2)",
                  "FFTConvPdf::signalFail(m_vis,DoubleCBFail,BW)",
              ]
          )             

  elif sig_model == 'BWDoubleCBConvCorr_TwoPeaks':
      nparams = 15
      pdf_args.extend(
              [
                  "BreitWigner::BW(m_vis, meanbw[0], widthbw[2.495])",
                  "CBShape::CBPass1(m_vis, mean[90,80,100], sigma[2,0.2,4], alpha[1,-50,50], n[1,0,50])",
                  "CBShape::CBPass2(m_vis, meanp[90,80,100], sigmap[4,4,10], alphap[1,-50,50], np[1,0,50])",
                  "SUM::DoubleCBPass(CBPass1, vFracp[0.01,0,1]*CBPass2)",
                  "FFTConvPdf::signalPass(m_vis,DoubleCBPass,BW)",
                  "CBShape::CBFail1(m_vis, mean[90,80,100], sigma[2,0.2,4], alpha[1,-50,50], n[1,0,50])",
                  "CBShape::CBFail2(m_vis, meanf[80,75,90], sigmaf[8,1,15], alphaf[1,-50,50], nf[1,0,50])",
                  "SUM::DoubleCBFail(CBFail1, vFracf[0.2,0,1]*CBFail2)",
                  "FFTConvPdf::signalFail(m_vis,DoubleCBFail,BW)",
              ]
          )             

  elif sig_model == 'BWDoubleCBConvUnCorr_TwoPeaks':
      nparams = 15
      pdf_args.extend(
              [
                  "BreitWigner::BW(m_vis, meanbw[0], widthbw[2.495])",
                  "CBShape::CBPass1(m_vis, meanp1[90,80,100], sigmap1[2,1,4], alphap1[1,-50,50], np1[1,0,50])",
                  "CBShape::CBPass2(m_vis, meanp2[90,80,100], sigmap2[4,4,10], alphap2[1,-50,50], np2[1,0,50])",
                  "SUM::DoubleCBPass(CBPass1, vFracp[0.01,0,1]*CBPass2)",
                  "FFTConvPdf::signalPass(m_vis,DoubleCBPass,BW)",
                  "CBShape::CBFail1(m_vis, meanf1[90,80,100], sigmaf1[2,1,4], alphaf1[1,-50,50], nf1[1,0,50])",
                  "CBShape::CBFail2(m_vis, meanf2[80,75,90], sigmaf2[8,1,15], alphaf2[1,-50,50], nf2[1,0,50])",
                  "SUM::DoubleCBFail(CBFail1, vFracf[0.2,0,1]*CBFail2)",
                  "FFTConvPdf::signalFail(m_vis,DoubleCBFail,BW)",
              ]
          )             


  elif sig_model == 'BWCBGausConvCorr':
      nparams = 11
      pdf_args.extend(
              [
                  "BreitWigner::BW(m_vis, meanbw[0], widthbw[2.495])",
                  "CBShape::CBPass(m_vis, mean[90,80,100], sigma[2,1,4], alpha[1,-50,50], n[1,0,50])",
                  "Gaussian::GaussPass(m_vis, meanp[90,80,100], sigmap[4,2,10])",
                  "SUM::DoubleCBPass(CBPass, vFracp[0.01,0,1]*GaussPass)",
                  "FFTConvPdf::signalPass(m_vis,DoubleCBPass,BW)",
                  "CBShape::CBFail(m_vis, mean[90,80,100], sigma[2,1,4], alpha[1,-50,50], n[1,0,50])",
                  "Gaussian::GaussFail(m_vis, meanf[90,80,100], sigmaf[4,2,10])",
                  "SUM::DoubleCBFail(CBFail, vFracf[0.01,0,1]*GaussFail)",
                  "FFTConvPdf::signalFail(m_vis,DoubleCBFail,BW)",
              ]
          ) 
  elif sig_model == 'BWCBGausConvUncorr':
      nparams = 15
      pdf_args.extend(
              [
                  "BreitWigner::BW(m_vis, meanbw[0], widthbw[2.495])",
                  "CBShape::CBPass(m_vis, meanp1[90,80,100], sigmap1[2,1,4], alphap[1,-50,50], np[1,0,50])",
                  "Gaussian::GaussPass(m_vis, meanp2[90,80,100], sigmap2[4,2,10])",
                  "SUM::DoubleCBPass(CBPass, vFracp[0.01,0,1]*GaussPass)",
                  "FFTConvPdf::signalPass(m_vis,DoubleCBPass,BW)",
                  "CBShape::CBFail(m_vis, meanf1[90,80,100], sigmaf1[2,1,4], alphaf[1,-50,50], nf[1,0,50])",
                  "Gaussian::GaussFail(m_vis, meanf2[90,80,100], sigmaf2[4,2,10])",
                  "SUM::DoubleCBFail(CBFail, vFracf[0.01,0,1]*GaussFail)",
                  "FFTConvPdf::signalFail(m_vis,DoubleCBFail,BW)",
              ]
          )    
  elif sig_model == 'DoubleVUncorr_embedsel':
      nparams = 10
      pdf_args.extend(
              [
                  "Voigtian::signal1Pass(m_vis, meanp1[90,85,95], widthp1[2.495], sigma1p[0.9,0.5,3])",
                  "Voigtian::signal2Pass(m_vis, meanp2[90,85,95], widthp2[2.495], sigma2p[4,3,10])",
                  "SUM::signalPass(vFracp[0.7,0.5,1]*signal1Pass, signal2Pass)",
                  "Voigtian::signal1Fail(m_vis, meanf1[90,85,95], widthfq[2.495], sigma1f[0.9,0.5,3])",
                  "Voigtian::signal2Fail(m_vis, meanf2[90,85,95], widthf2[2.495], sigma2f[4,3,10])",
                  "SUM::signalFail(vFracf[0.7,0.5,1]*signal1Fail, signal2Fail)"
              ]
          )   
  elif sig_model == 'DoubleVUncorr_UL':
      nparams = 10
      pdf_args.extend(
              [
                  "Voigtian::signal1Pass(m_vis, meanp1[90,80,95], widthp1[2.495], sigma1p[0.9,0.5,3])",
                  "Voigtian::signal2Pass(m_vis, meanp2[90,80,95], widthp2[2.495], sigma2p[4,3,10])",
                  "vFracp[1.0,0.25,1.0]", 
                  "SUM::signalPass(vFracp*signal1Pass, expr('1-vFracp',vFracp)*signal2Pass)",
                  "Voigtian::signal1Fail(m_vis, meanf1[90,80,95], widthfq[2.495], sigma1f[0.9,0.5,3])",
                  "Voigtian::signal2Fail(m_vis, meanf2[90,80,95], widthf2[2.495], sigma2f[4,3,10])",
                  "vFracf[1.0,0.25,1.0]", 
                  "SUM::signalFail(vFracf*signal1Fail, expr('1-vFracf',vFracf)*signal2Fail)",
                  #"SUM::signalFail(signal1Fail, vFracf[0.0,0.0,1.0]*signal2Fail)"
              ]
          )      
  elif sig_model == 'VUncorr_UL':
      nparams = 4
      pdf_args.extend(
              [
                  "Voigtian::signalPass(m_vis, meanp1[90,80,95], widthp1[2.495], sigma1p[0.9,0.5,3])",
                  "Voigtian::signalFail(m_vis, meanf1[90,80,95], widthfq[2.495], sigma1f[0.9,0.5,3])",
              ]
          ) 
  elif sig_model == 'BWCBConvUncorr_UL':
      nparams = 9
      pdf_args.extend(
              [
                  "BreitWigner::BW(m_vis, meanbw[0], widthbw[2.495])",
                  "CBShape::CBPass(m_vis, meanp[90,80,95], sigmap[0.9,0.5,3], alphap[1,0,50], np[1,0,50])",
                  "FFTConvPdf::signalPass(m_vis,CBPass,BW)",
                  "CBShape::CBFail(m_vis, meanf[90,80,95], sigmaf[0.9,0.5,3], alphaf[1,0,50], nf[1,0,50])",
                  "FFTConvPdf::signalFail(m_vis,CBFail,BW)",
              ]
          )


  elif sig_model == 'BWDoubleCBConvCorr_UL':
      nparams = 15
      pdf_args.extend(
              [   
                  "BreitWigner::BW(m_vis, meanbw[0], widthbw[2.495])",
                  "CBShape::CBPass1(m_vis, mean[90,80,100], sigma[2,1,4], alpha[1,-50,50], n[1,0,50])",
                  "CBShape::CBPass2(m_vis, meanp[90,70,100], sigmap[4,4,10], alphap[1,-50,50], np[1,0,50])",
                  "SUM::DoubleCBPass(CBPass1, vFracp[0.01,0,1]*CBPass2)",
                  "FFTConvPdf::signalPass(m_vis,DoubleCBPass,BW)",
                  "CBShape::CBFail1(m_vis, mean[90,80,100], sigma[2,1,4], alpha[1,-50,50], n[1,0,50])",
                  "CBShape::CBFail2(m_vis, meanf[90,70,100], sigmaf[4,4,10], alphaf[1,-50,50], nf[1,0,50])",
                  "SUM::DoubleCBFail(CBFail1, vFracf[0.01,0,1]*CBFail2)",
                  "FFTConvPdf::signalFail(m_vis,DoubleCBFail,BW)",
              ]
          )

            
  if bkg_model == 'Exponential':
      nparams += 2        
      pdf_args.extend(
              [
                  "Exponential::backgroundPass(m_vis, lp[-0.1,-1,0])",
                  "Exponential::backgroundFail(m_vis, lf[-0.1,-1,0])"
              ]
          )
  elif bkg_model == 'CMSShape':
      nparams += 4
      pdf_args.extend(
              [
                  "RooCMSShape::backgroundPass(m_vis, alphaPass[70,60,200], betaPass[0.001,0,0.1], gammaPass[0.001,0,1], peak[90])",
                  "RooCMSShape::backgroundFail(m_vis, alphaFail[70,60,200], betaFail[0.001,0,0.1], gammaFail[0.001,0,1], peak[90])",
                  # attenmpt to limit shape to peak below 90 GeV: beta_max = 90./1000.*gamma              #90./1000.*gammaPass,
                  #betaFail=62.1537
                  #Parameter betaFail  has zero or invalid step size - consider it as constant
                  #"expr::betaMaxPass('gammaPass*90./1000',gammaPass[0.001,0,1])",
                  #"expr::betaMaxPass('gammaPass2*0.1',gammaPass2[1])",
                  #"RooCMSShape::backgroundPass(m_vis, alphaPass[70,60,200], betaPass[0.001,0,betaMaxPass], gammaPass[0.001,0,1], peak[90])"
                  #"RooCMSShape::backgroundFail(m_vis, alphaFail[70,60,200], betaFail[0.001,0,min(0.0011,gammaFail*90./1000.)], gammaFail[0.001,0,1], peak[90])",
                  #"RooCMSShape::backgroundPass(m_vis, alphaPass[70,60,200], betaPass[0.001,0,gammaPass], gammaPass[0.001,0,1], peak[90])",
                  #"RooCMSShape::backgroundFail(m_vis, alphaFail[70,60,200], betaFail[0.001,0,0.1], gammaFail[0.001,0,1], peak[90])",
              ]
          )
  elif bkg_model == 'Chebychev':
      pdf_args.extend(
              [
                  "RooChebychev::backgroundPass(m_vis, {a0p[0.25,0,0.5], a1p[-0.25,-1,0.1],a2p[0.,-0.25,0.25]})",
                  "RooChebychev::backgroundFail(m_vis, {a0f[0.25,0,0.5], a1f[-0.25,-1,0.1],a2f[0.,-0.25,0.25]})",
              ]
          )
  
  for arg in pdf_args:
    wsp.factory(arg)
  nparams=0
  model_args = [
      "expr::nSignalPass('efficiency*fSigAll*numTot',efficiency[0,1], fSigAll[0.9,0,1],numTot[1,0,1e10])",
      "expr::nSignalFail('(1-efficiency)*fSigAll*numTot',efficiency,fSigAll,numTot)",
      "expr::nBkgPass('effBkg*(1-fSigAll)*numTot',effBkg[0.9,0,1],fSigAll,numTot)",
      "expr::nBkgFail('(1-effBkg)*(1-fSigAll)*numTot',effBkg,fSigAll,numTot)",
      "SUM::passing(nSignalPass*signalPass,nBkgPass*backgroundPass)",
      "SUM::failing(nSignalFail*signalFail,nBkgFail*backgroundFail)",
      "cat[fail,pass]",
      "SIMUL::model(cat,fail=failing,pass=passing)"
  ]
  for arg in model_args:
    wsp.factory(arg)
  
  hist2d = infile.Get(name+'/%s_eff' % name)
  res = []
  
  for i in range(1,hist2d.GetNbinsX()+1):
    for j in range(1,hist2d.GetNbinsY()+1):
      bin_low_edge = str(round(hist2d.GetYaxis().GetBinLowEdge(j),1)).replace(".","p")
      bin_up_edge  = str(round(hist2d.GetYaxis().GetBinUpEdge(j),1)).replace(".","p")
      if "id" in name: path = options.outputfolder + "/id/" + name +"_eta_{}_to_{}".format(bin_low_edge,bin_up_edge)
      elif "iso" in name: path = options.outputfolder + "/iso/" + name +"_eta_{}_to_{}".format(bin_low_edge,bin_up_edge)
      else: path = options.outputfolder + "/trg/" + name +"_eta_{}_to_{}".format(bin_low_edge,bin_up_edge)

      if not os.path.exists(path):
         os.makedirs(path)

      xmin = hist2d.GetXaxis().GetBinLowEdge(i)    
      xmax = hist2d.GetXaxis().GetBinUpEdge(i)
      ymin = hist2d.GetYaxis().GetBinLowEdge(j)
      ymax = hist2d.GetYaxis().GetBinUpEdge(j)  
      
      ForceEventCount = False
      #if options.era in ['UL_17','UL_18'] and ('_trg' in name or '_iso' in name) and options.channel == 'tpzee': 
      #    if xmin >= 50: ForceEventCount = True
      #if options.era in ['UL_18'] and ('_iso' in name) and options.channel == 'tpzmm':
      #    if xmin >= 50: ForceEventCount = True

      dat = '%s_pt_%.0f_to_%.0f_eta_%.1f_to_%.1f' % (name,xmin,xmax,ymin,ymax)    
      yield_tot = wsp.data(dat).sumEntries()
      yield_pass = wsp.data(dat).sumEntries("cat==cat::pass")
      wsp.var("numTot").setVal(yield_tot)
      if yield_tot>0: 
        wsp.var("efficiency").setVal(yield_pass/yield_tot)
        wsp.var("efficiency").setError(math.sqrt(yield_pass)/yield_tot) #not quite correct error
      else: 
        wsp.var("efficiency").setVal(0.)
        wsp.var("efficiency").setError(0.) 
        ForceEventCount = True # dont do fit if yield is 0 anyway
    
      if options.channel=='tpzee' and 'id' in name and options.era == 'UL_17' and scenario == "nominal":
        if xmin>=100: 
          print 'changing sigma2f parameter'
          wsp.var('sigma1f').setRange(0.2,4)
          wsp.var('sigma2f').setRange(2,15)
          wsp.var('sigma2p').setRange(2,10)
        elif xmin >= 40:
          wsp.var('sigma2f').setRange(0.2,10)
          wsp.var('sigma1f').setRange(0.2,10)
          wsp.var('sigma2p').setRange(0.2,10)
        elif xmin>=50 and xmin<100:
          print 'changing sigmaf parameters'
          wsp.var('sigma2f').setRange(0.2,10)
          wsp.var('sigma1f').setRange(0.2,10)
          wsp.var('sigma2p').setRange(2,10)
        else: 
          wsp.var('sigma1f').setRange(0.2,4)
          wsp.var('sigma2f').setRange(2,10)
          wsp.var('sigma2p').setRange(2,10)

      if doFit and not ForceEventCount:
        wsp.pdf("model").fitTo(wsp.data(dat),
                               ROOT.RooFit.Optimize(False),
                               ROOT.RooFit.Minimizer("Minuit2", "Migrad"),
                               ROOT.RooFit.Offset(True),
                               ROOT.RooFit.Extended(True),
                               ROOT.RooFit.SumW2Error(False),
                               ROOT.RooFit.PrintLevel(-1))
        
        fitres = wsp.pdf("model").fitTo(wsp.data(dat),
                                        ROOT.RooFit.Minimizer("Minuit2", "Migrad"),
                                        ROOT.RooFit.Optimize(False),
                                        ROOT.RooFit.Offset(True),
                                        ROOT.RooFit.Extended(True),
                                        ROOT.RooFit.PrintLevel(-1),
                                        ROOT.RooFit.SumW2Error(False),
                                        ROOT.RooFit.Save())
        fitres.Print()
        
        canv = ROOT.TCanvas('%s' % (dat), "%s" % (dat), 0, 0, 700, 400)
        #canv.SetTopMargin(40)
        pad_left = ROOT.TPad('left', '', 0., 0., 0.5, 0.97)
        pad_left.SetTicky(1)
        pad_left.SetTickx(1)
        pad_left.Draw()
        pad_right = ROOT.TPad('right', '', 0.5, 0., 1., 0.97)
        pad_right.SetTicky(1)
        pad_right.SetTickx(1)
        pad_right.Draw()
        pads = [pad_left, pad_right]
        
        latex = ROOT.TLatex()
        latex.SetNDC()
        
        ROOT.TGaxis.SetExponentOffset(-0.08, -0.02)
        
        splitData = wsp.data(dat).split(wsp.cat('cat'))
        xframe = wsp.var("m_vis").frame(ROOT.RooFit.Title("Passing"))
        width = (wsp.var("m_vis").getMax() - wsp.var("m_vis").getMin()) / splitData.At(1).numEntries()
        splitData.At(1).plotOn(xframe, ROOT.RooFit.Name("DataPass"),ROOT.RooFit.MarkerStyle(7))
        wsp.pdf("passing").plotOn(xframe,
                                  ROOT.RooFit.Slice(wsp.cat('cat'), "pass"),
                                  ROOT.RooFit.LineColor(ROOT.kBlue),
                                  ROOT.RooFit.Name("AllPass"))
        wsp.pdf("passing").plotOn(xframe,
                                  ROOT.RooFit.Slice(wsp.cat('cat'), "pass"),
                                  ROOT.RooFit.Components('backgroundPass'),
                                  ROOT.RooFit.LineStyle(ROOT.kDashed),
                                  ROOT.RooFit.LineColor(ROOT.kBlue),
                                  ROOT.RooFit.Name("BkgPass"))
        splitData.At(1).plotOn(xframe, ROOT.RooFit.Name("DataPass"),ROOT.RooFit.MarkerStyle(7))
        pads[0].cd()
        
        xframe.Draw()
        
        axis = plotting.GetAxisHist(pads[0])
        if options.channel == 'tpzee':
          plotting.Set(axis.GetXaxis().SetTitle('m_{ee} (GeV)'))
        else:
          plotting.Set(axis.GetXaxis().SetTitle('m_{#mu#mu} (GeV)'))
        plotting.Set(axis.GetYaxis().SetTitle('Events / %g GeV' % width))
        plotting.Set(axis.SetTitle(''))
        plotting.Set(axis.GetYaxis().SetTitleOffset(1.4))
        
        titlelatex = ROOT.TLatex()
        titlelatex.SetNDC()
        titlelatex.SetTextSize(0.035)
        titlelatex.DrawLatex(0.12, 0.97, '%g < p_{T} < %g GeV, %g < |#eta| < %g' % (xmin, xmax, ymin, ymax))
        
        latex.SetTextSize(0.035)
        font = latex.GetTextFont()
        latex.DrawLatex(0.16, 0.84, 'Pass Region')
        latex.SetTextFont(42)
        #latex.DrawLatex(0.6, 0.75, '#chi^{2} = %.2f' % (xframe.chiSquare("AllPass", "DataPass", nparams)))
        latex.DrawLatex(0.58, 0.7, '#varepsilon = %.4f #pm %.4f' % (wsp.var('efficiency').getVal(), wsp.var('efficiency').getError()))
        ROOT.gStyle.SetLegendBorderSize(1)
        legend1 = ROOT.TLegend(0.6, 0.8, 0.925, 0.939)
        legend1.AddEntry(xframe.findObject("DataPass"), "data", "lep")
        if options.channel == 'tpzee': legend1.AddEntry(xframe.findObject("AllPass"), "Z #rightarrow ee + BG", "l")
        else: legend1.AddEntry(xframe.findObject("AllPass"), "Z #rightarrow #mu#mu + BG", "l")
        legend1.AddEntry(xframe.findObject("BkgPass"), "BG", "l")
        legend1.Draw()
        xframe2 = wsp.var("m_vis").frame(ROOT.RooFit.Title("Failing")) 
        splitData.At(0).plotOn(xframe2, ROOT.RooFit.Name("DataFail"),ROOT.RooFit.MarkerStyle(7))
        wsp.pdf("failing").plotOn(xframe2,
                                  ROOT.RooFit.Slice(wsp.cat('cat'), "fail"),
                                  ROOT.RooFit.LineColor(ROOT.kRed),
                                  ROOT.RooFit.Name("AllFail"))
        wsp.pdf("failing").plotOn(xframe2,
                                  ROOT.RooFit.Slice(wsp.cat('cat'), "fail"),
                                  ROOT.RooFit.Components('backgroundFail'),
                                  ROOT.RooFit.LineStyle(ROOT.kDashed),
                                  ROOT.RooFit.LineColor(ROOT.kRed),
                                  ROOT.RooFit.Name("BkgFail"))
        splitData.At(0).plotOn(xframe2, ROOT.RooFit.Name("DataFail"),ROOT.RooFit.MarkerStyle(7))
        #splitData.At(0).plotOn(xframe, ROOT.RooFit.Name("DataFail"),ROOT.RooFit.MarkerStyle(7))

        pads[1].cd()
        xframe2.Draw()
        axis = plotting.GetAxisHist(pads[1])
        if options.channel== 'tpzee':
            plotting.Set(axis.GetXaxis().SetTitle('m_{ee} (GeV)'))
        else:
            plotting.Set(axis.GetXaxis().SetTitle('m_{#mu#mu} (GeV)'))
        plotting.Set(axis.GetYaxis().SetTitle('Events / %g GeV' % width))
        plotting.Set(axis.SetTitle(''))
        plotting.Set(axis.GetYaxis().SetTitleOffset(1.4))
        ROOT.TGaxis().SetMaxDigits(3)
        ROOT.TGaxis().SetExponentOffset(0., 0.01, "y");
        
        
        #latex.DrawLatex(0.6, 0.75, '#chi^{2} = %.2f' % (xframe2.chiSquare("AllFail", "DataFail", nparams)))
        latex.SetTextFont(font)
        latex.DrawLatex(0.16, 0.84, 'Fail Region')
        
        
        legend2 = ROOT.TLegend(0.6, 0.8, 0.925, 0.939)
        legend2.AddEntry(xframe2.findObject("DataFail"), "data", "lep")
        if options.channel == 'tpzee': legend2.AddEntry(xframe2.findObject("AllFail"), "Z #rightarrow ee + BG", "l")
        else: legend2.AddEntry(xframe2.findObject("AllFail"), "Z #rightarrow #mu#mu + BG", "l")
        legend2.AddEntry(xframe2.findObject("BkgFail"), "BG", "l")
        legend2.Draw()
        
        if "id" in name: canv.Print(options.outputfolder + "/id/" + name + "_eta_{}_to_{}".format(bin_low_edge,bin_up_edge) +'/'+dat+'_'+options.channel+"_"+scenario+'.pdf')
        elif "iso" in name: canv.Print(options.outputfolder + "/iso/"+ name + "_eta_{}_to_{}".format(bin_low_edge,bin_up_edge) +'/'+dat+'_'+options.channel+"_"+scenario+'.pdf')
        else: canv.Print(options.outputfolder + "/trg/" + name + "_eta_{}_to_{}".format(bin_low_edge,bin_up_edge) +'/'+dat+'_'+options.channel+"_"+scenario+'.pdf')
 
        del canv
        
      res.append((dat, wsp.var('efficiency').getVal(), wsp.var('efficiency').getError()))
      hist2d.SetBinContent(i,j,wsp.var('efficiency').getVal())
      hist2d.SetBinError(i,j,wsp.var('efficiency').getError())
       
 
  outfile.cd()
  for i in xrange(1, hist2d.GetNbinsY()+1):
    ymin = hist2d.GetYaxis().GetBinLowEdge(i)    
    ymax = hist2d.GetYaxis().GetBinUpEdge(i)  
    slice = hist2d.ProjectionX(('%s_eta_%.1f_to_%.1f' % (hist2d.GetName(), ymin, ymax)).replace('.','p'), i, i)
    slice.SetTitle('%.1f #ge |#eta| < %.1f' % (ymin,ymax))
    gr = ROOT.TGraphAsymmErrors(slice)
    gr.SetName('gr_'+slice.GetName())
    gr.Write()
  hist2d.Write()
    
# Add data sample names
if options.channel == 'tpzmm': 
    if options.era == 'UL_16preVFP':
        data_samples = ['SingleMuonB','SingleMuonC','SingleMuonD','SingleMuonE','SingleMuonF']
    elif options.era == 'UL_16postVFP':
        data_samples = ['SingleMuonF','SingleMuonG','SingleMuonH']
    elif options.era == 'UL_17':
        data_samples = ['SingleMuonB','SingleMuonC','SingleMuonD','SingleMuonE','SingleMuonF']
    elif options.era == 'UL_18':
        data_samples = ['SingleMuonA','SingleMuonB','SingleMuonC','SingleMuonD']
    
if  options.channel == 'tpzee': 
    if options.era == 'UL_16preVFP': data_samples = ['SingleElectronB','SingleElectronC','SingleElectronD','SingleElectronE','SingleElectronF']
    elif options.era == 'UL_16postVFP': data_samples = ['SingleElectronF','SingleElectronG','SingleElectronH']    
    elif options.era == 'UL_17': data_samples = ['SingleElectronB','SingleElectronC','SingleElectronD','SingleElectronE','SingleElectronF']
    elif options.era == 'UL_18': data_samples = ['EGammaA','EGammaB','EGammaC','EGammaD']

embed_samples = []
if options.channel == "tpzmm":
  if options.era == "UL_18":
    embed_samples = ["EmbeddingMuMu2018A","EmbeddingMuMu2018B","EmbeddingMuMu2018C","EmbeddingMuMu2018D"]
  if options.era == "UL_17":
    embed_samples = ["EmbeddingMuMu2017B","EmbeddingMuMu2017C","EmbeddingMuMu2017D","EmbeddingMuMu2017E","EmbeddingMuMu2017F"]
  if options.era == "UL_16preVFP":
    embed_samples = ["EmbeddingMuMu2016-HIPM_B_ver2","EmbeddingMuMu2016-HIPM_C","EmbeddingMuMu2016-HIPM_D","EmbeddingMuMu2016-HIPM_E","EmbeddingMuMu2016-HIPM_F"]
  if options.era == "UL_16postVFP":
    embed_samples = ["EmbeddingMuMu2016F","EmbeddingMuMu2016G","EmbeddingMuMu2016H"]

# Add MC sample names   
if options.era == 'UL_16preVFP':  ztt_samples = ['DYJetsToLL-LO']
elif options.era == 'UL_16postVFP': ztt_samples = ['DYJetsToLL-LO']
elif options.era == 'UL_17':  ztt_samples = ['DYJetsToLL-LO','DYJetsToLL-LO-ext1']
elif options.era == 'UL_18': ztt_samples = ['DYJetsToLL-LO','DYJetsToLL-LO-ext1']

#Formula:  abs(eta_2),pt_2,m_vis[0,0.1,0.3,0.8,1.0,1.2,1.6,1.8,2.1,2.4],[10,15,17,19,21,23,24,25,26,27,28,31,34,37,40,45,50,60,70,100,1000],(40,70,110) (wt)*((m_vis>50&&m_vis<150&&pt_1>28&&abs(eta_1)<2.1&&iso_1<0.15&&id_tag_1&&trg_tag_1&&os)*(1&&id_probe_1))*(os)*(1)*(!(trg_probe_2))
ROOT.TH1.SetDefaultSumw2(True)

trg_probe_1 = '(trg_probe_1)'
trg_probe_2 = '(trg_probe_2)'
if options.embed_sel:
  trg_probe_1 = '(trg_probe_1)'
  trg_probe_2 = '(trg_probe_2)'
if options.embed_dz:
  trg_probe_1 = '(pass_dz)'
  trg_probe_2 = '(pass_dz)'
id_probe_1 = '(id_probe_1)'
id_probe_2 = '(id_probe_2)'

if options.channel == 'tpzmm':
  iso_cut_1='iso_1<0.15'
  iso_cut_2='iso_2<0.15'
  
  if options.era in ['UL_17','UL_18']:
    baseline_tag1 = '(m_vis>50&&m_vis<150&&pt_1>28&&abs(eta_1)<2.1&&iso_1<0.15&&id_tag_1&&trg_tag_1&&os)'
    baseline_tag2 = '(m_vis>50&&m_vis<150&&pt_2>28&&abs(eta_2)<2.1&&iso_2<0.15&&id_tag_2&&trg_tag_2&&os)'
  else:
    baseline_tag1 = '(m_vis>50&&m_vis<150&&pt_1>25&&abs(eta_1)<2.1&&iso_1<0.15&&id_tag_1&&trg_tag_1&&os)'
    baseline_tag2 = '(m_vis>50&&m_vis<150&&pt_2>25&&abs(eta_2)<2.1&&iso_2<0.15&&id_tag_2&&trg_tag_2&&os)'

  if options.embed_sel:
    iso_cut_1="1"
    iso_cut_2="1"
     
if options.channel == 'tpzee':
  if options.era in ['UL_16preVFP','UL_16postVFP','UL_17','UL_18']:
    iso_cut_1='iso_1<0.15'
    iso_cut_2='iso_2<0.15'
  
  if options.era in ['UL_17','UL_18']:
    if options.tree_name == 'tagandprobe_ET':
      baseline_tag1 = '(m_vis>50&&m_vis<150&&pt_1>36&&abs(eta_1)<2.1&&iso_1<0.1&&id_tag_1&&trg_tag_1&&trg_tag_extra_1&&os)'
      baseline_tag2 = '(m_vis>50&&m_vis<150&&pt_2>36&&abs(eta_2)<2.1&&iso_2<0.1&&id_tag_2&&trg_tag_2&&trg_tag_extra_2&&os)'
    else:
      if options.tight_tag:
         baseline_tag1 = '(m_vis>50&&m_vis<150&&pt_1>40&&abs(eta_1)<2.1&&iso_1<0.1&&id_tag_1&&trg_tag_1&&os)'
         baseline_tag2 = '(m_vis>50&&m_vis<150&&pt_2>40&&abs(eta_2)<2.1&&iso_2<0.1&&id_tag_2&&trg_tag_2&&os)'
      else:
         baseline_tag1 = '(m_vis>50&&m_vis<150&&pt_1>36&&abs(eta_1)<2.1&&iso_1<0.1&&id_tag_1&&trg_tag_1&&os)'
         baseline_tag2 = '(m_vis>50&&m_vis<150&&pt_2>36&&abs(eta_2)<2.1&&iso_2<0.1&&id_tag_2&&trg_tag_2&&os)'
  else:    
    if options.tight_tag:
       baseline_tag1 = '(m_vis>50&&m_vis<150&&pt_1>40&&abs(eta_1)<2.1&&iso_1<0.1&&id_tag_1&&trg_tag_1&&os)'
       baseline_tag2 = '(m_vis>50&&m_vis<150&&pt_2>40&&abs(eta_2)<2.1&&iso_2<0.1&&id_tag_2&&trg_tag_2&&os)'
    else:
       baseline_tag1 = '(m_vis>50&&m_vis<150&&pt_1>25&&abs(eta_1)<2.1&&iso_1<0.1&&id_tag_1&&trg_tag_1&&os)'
       baseline_tag2 = '(m_vis>50&&m_vis<150&&pt_2>25&&abs(eta_2)<2.1&&iso_2<0.1&&id_tag_2&&trg_tag_2&&os)'

iso_probe_1 = '(%s)' % iso_cut_1
iso_probe_2 = '(%s)' % iso_cut_2

idiso_probe_1 = '(%s && %s)' % (id_probe_1,iso_cut_1)
idiso_probe_2 = '(%s && %s)' % (id_probe_2,iso_cut_2)

id_tag_1 = baseline_tag1 
id_tag_2 = baseline_tag2 
idiso_tag_1 = baseline_tag1 
idiso_tag_2 = baseline_tag2 
iso_tag_1 = baseline_tag1+'*(id_probe_2)'
iso_tag_2 = baseline_tag2+'*(id_probe_1)'
fix_iso_tag_1 = baseline_tag1+'*(id_probe_2)'
fix_iso_tag_2 = baseline_tag2+'*(id_probe_1)'
if (options.veto_FSR==True):
    if options.channel == 'tpzee':
        iso_tag_1+='*(!(pass_FSR_condition==1 && m_gamma_leptons>80 && m_gamma_leptons<100))'
        iso_tag_2+='*(!(pass_FSR_condition==1 && m_gamma_leptons>80 && m_gamma_leptons<100))'
    else:
        iso_tag_1+='*(!(pass_FSR_condition==1 && m_gamma_muons>80 && m_gamma_muons<100))'
        iso_tag_2+='*(!(pass_FSR_condition==1 && m_gamma_muons>80 && m_gamma_muons<100))'

    if options.embedded:
        fix_iso_tag_1+='*(!(pass_FSR_condition==1 && m_gamma_leptons>80 && m_gamma_leptons<100))'
        fix_iso_tag_2+='*(!(pass_FSR_condition==1 && m_gamma_leptons>80 && m_gamma_leptons<100))'

trg_tag_1 = baseline_tag1+'*(%s&&id_probe_2)' % iso_cut_2
trg_tag_2 = baseline_tag2+'*(%s&&id_probe_1)' % iso_cut_1
if options.embed_dz:
  trg_tag_1= 'm_vis>50&&m_vis<150&&pt_1>28&&pt_2>28&&abs(eta_1)<2.4&&abs(eta_2)<2.4&&id_tag_1&&id_tag_2&&trg_tag_1&&os&&pass_dimu'
  trg_tag_2='0'

# Create output file
output_name = options.outputfolder+'/tagandprobe_'+options.channel+'.root'
if options.tight_tag: output_name = options.outputfolder+'/tagandprobe_'+options.channel+'_tightTag.root'

nodename = options.channel
if options.draw_hists == 1:
    outfile = ROOT.TFile(output_name, 'RECREATE')
    ana = Analysis()
    ana.nodes.AddNode(ListNode(nodename))
    
    ana.remaps = {}
    if options.channel =='tpzmm': ana.remaps['SingleMuon'] = 'data_obs'
    elif options.channel == 'tpzee':
        if options.era in ['UL_18']: ana.remaps['EGamma'] = 'data_obs'
        else: ana.remaps['SingleElectron'] = 'data_obs'
    
    # Add all data files
    for sample_name in data_samples:
        ana.AddSamples(options.folder+'/'+sample_name+'_'+options.channel+'*.root', options.tree_name, None, sample_name)
    
    # Add all MC background files
    for sample_name in ztt_samples:
    	ana.AddSamples(options.folder+'/'+sample_name+'_'+options.channel+'*.root', options.tree_name, None, sample_name)

    if options.embedded:
      # Add all embedded files
      for sample_name in embed_samples:
          ana.AddSamples(options.folder+'/'+sample_name+'_'+options.channel+'*.root', options.tree_name, None, sample_name)
    
    Produce3DHistograms(ana, 'wt', outfile)
else:
    outfile = ROOT.TFile(output_name)

wsfilename = output_name.replace('.root','_ws.root')
wsfilename_sig = output_name.replace('.root','_ws_sig.root')
wsfilename_bkg = output_name.replace('.root','_ws_bkg.root')

wsfile = ROOT.TFile(wsfilename, 'RECREATE')
wsfile_sig = ROOT.TFile(wsfilename_sig, 'RECREATE')
wsfile_bkg = ROOT.TFile(wsfilename_bkg, 'RECREATE')

if options.tight_tag:
   wsfilename_tightTag = output_name.replace('.root','_ws_tightTag.root')
   wsfile_tightTag = ROOT.TFile(wsfilename_tightTag, 'RECREATE')

if not options.embed_sel:
  wsnames = ['data_id', 'ZLL_id', 'data_iso', 'ZLL_iso', 'data_trg', 'ZLL_trg']
  if options.trg_only: wsnames = ['data_trg', 'ZLL_trg']
else: 
  wsnames = ['data_id', 'data_trg']
  if options.trg_only: wsnames = ['data_trg']
if options.embedded: 
  if options.trg_only: wsnames += ['embed_trg']
  else: wsnames += ['embed_id', 'embed_iso', 'embed_trg']

for name in wsnames: CreateWorkspace(name, outfile, wsfile)
for name in wsnames: CreateWorkspace(name, outfile, wsfile_sig)
for name in wsnames: CreateWorkspace(name, outfile, wsfile_bkg)

if options.tight_tag:
   for name in wsnames: CreateWorkspace(name, outfile, wsfile_tightTag)

sffile_name = options.outputfolder+'/muon_SFs.root'
if options.channel == 'tpzee': sffile_name = options.outputfolder+'/electron_SFs.root'

variations = ["nominal","signal","bkg"]
if options.tight_tag: variations = ["tightTag"]

for i in variations:
   object_name = "electron" if options.channel=="tpzee" else "muon"
   if i == "nominal": sffile_name = options.outputfolder+'/{}_nom.root'.format(object_name) 
   if i == "signal" : sffile_name = options.outputfolder+'/{}_sig.root'.format(object_name)
   if i == "bkg"    : sffile_name = options.outputfolder+'/{}_bkg.root'.format(object_name)
   if i == "tightTag": sffile_name = options.outputfolder+'/{}_tightTag.root'.format(object_name)

   sffile = ROOT.TFile(sffile_name, 'RECREATE')
   
   for name in wsnames:
      if options.channel == "tpzee":
         sig_model = 'BWDoubleCBConvCorr'
         if i == "signal": sig_model = "DoubleVUncorr"
         bkg_model = 'CMSShape'

         if options.era in ["UL_17"]:
            if i == "signal": sig_model = "BWCBConvCorr"
            else:
               if "id" in name: sig_model = "DoubleVUncorr"
               if "iso" in name: sig_model = "DoubleVUncorr_elec_TwoPeaks"
               if "trg" in name: sig_model = "DoubleVUncorr_elec"
            
         if options.era in ["UL_18"]:
            if i == "signal": sig_model = "BWCBConvCorr"
            else:
               if "id" in name: sig_model = "DoubleVUncorr_elec_18"
               if "iso" in name: sig_model = "DoubleVUncorr_elec_TwoPeaks"
               if "trg" in name: sig_model = "DoubleVUncorr_elec"

         if (i == "nominal" or i == "tightTag" or i =="signal") and "id" not in name: bkg_model = "Exponential"
         print(i,name,sig_model,bkg_model)
      
      elif options.channel == "tpzmm":
         if i == "signal": sig_model = "VUncorr_UL"
         else: sig_model = 'DoubleVUncorr_UL'

         if i == "bkg": bkg_model = "Exponential"
         else: bkg_model = 'CMSShape'
        
         if options.embed_sel or options.embed_dz:
           if i == "signal": sig_model = "VUncorr_UL" 
           else: sig_model='DoubleVUncorr_embedsel'

      if (not options.embed_dz or 'trg' in name or not options.trg_only or not ('iso' in name and options.embed_sel)):
         if i == "nominal": FitWorkspace(name,wsfile,sffile,sig_model,bkg_model,i,True)#'data' in name)
         if i == "signal": FitWorkspace(name,wsfile_sig,sffile,sig_model,bkg_model,i,True)#'data' in name)
         if i == "bkg": FitWorkspace(name,wsfile_bkg,sffile,sig_model,bkg_model,i,True)#'data' in name)
         if i == "tightTag": FitWorkspace(name,wsfile_tightTag,sffile,sig_model,bkg_model,i,True)#'data' in name)


   # now make plots os SFs and efficiencies vs pT:

   if options.channel == 'tpzmm': plot_name = 'muon_efficiency_'
   if options.channel == 'tpzee': plot_name = 'electron_efficiency_'
   
   sf_types = ['id','iso','trg']
   if options.embed_sel: sf_types = ['id','trg']
   if options.trg_only or options.embed_dz: sf_types = ['trg']
   
   for sf in sf_types:
     hist2d = sffile.Get('data_%s_eff' % sf)
     for j in range(1,hist2d.GetNbinsY()+1):
   
       ymin = hist2d.GetYaxis().GetBinLowEdge(j)
       ymax = hist2d.GetYaxis().GetBinUpEdge(j)
       if not options.embed_sel:
         leg_labels=['data','MC']
       else: leg_labels=['data']
       if not options.embed_sel:
         graphs = [sffile.Get(('gr_data_%s_eff_eta_%.1f_to_%.1f' % (sf,ymin,ymax)).replace('.','p')),sffile.Get(('gr_ZLL_%s_eff_eta_%.1f_to_%.1f' % (sf,ymin,ymax)).replace('.','p'))]
       else: graphs = [sffile.Get(('gr_data_%s_eff_eta_%.1f_to_%.1f' % (sf,ymin,ymax)).replace('.','p'))]
       if options.embedded:
         graphs.append(sffile.Get(('gr_embed_%s_eff_eta_%.1f_to_%.1f' % (sf,ymin,ymax)).replace('.','p')))
         leg_labels.append('Embedded')
       x_title = 'P_{T}^{#mu} (GeV)'
       ratio_range="0.7,1.3"
       if options.channel == 'tpzee':
           x_title = 'P_{T}^{e} (GeV)'
           if 'trg' in sf: ratio_range="0.1,2.0"
       label = '%s, %.1f < |#eta| < %.1f' % (sf, ymin,ymax)
       if options.channel == "tpzmm":
         if 'trg' in sf: label = 'Muon Trigger, %s, %.1f < |#eta| < %.1f' % (options.era,ymin,ymax)
         elif 'iso' in sf: label = 'Muon Iso, %s, %.1f < |#eta| < %.1f' % (options.era,ymin,ymax)
         elif 'id' in sf: label = 'Muon ID, %s, %.1f < |#eta| < %.1f' % (options.era,ymin,ymax)
       if options.channel == "tpzee":
         if 'trg' in sf: label = 'Electron Trigger, %s, %.1f < |#eta| < %.1f' % (options.era,ymin,ymax)
         elif 'iso' in sf: label = 'Electron Iso, %s, %.1f < |#eta| < %.1f' % (options.era,ymin,ymax)
         elif 'id' in sf: label = 'Electron ID, %s, %.1f < |#eta| < %.1f' % (options.era,ymin,ymax)
       plotting.TagAndProbePlot(graphs,leg_labels,"",True,False,options.era=='UL_18',ratio_range,True,200,10,False,0,1.5,x_title, "Efficiency",0,options.outputfolder+'/'+plot_name+sf+'_eta_%.1f_to_%.1f_%s'%(ymin,ymax,i),label)

   sffile.Close()

outfile.Close()  
wsfile.Close()
