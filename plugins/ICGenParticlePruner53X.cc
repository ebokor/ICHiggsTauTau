#include "FWCore/Framework/interface/EDProducer.h"
#include "FWCore/Utilities/interface/InputTag.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/Framework/interface/Event.h"
#include "DataFormats/Common/interface/Handle.h"
#include "DataFormats/HepMCCandidate/interface/GenParticle.h"
#include "CommonTools/Utils/interface/StringCutObjectSelector.h"
#include "FWCore/Utilities/interface/EDMException.h"
#include "PhysicsTools/HepMCCandAlgos/interface/PdgEntryReplacer.h"

namespace helper {
  struct SelectCode {
    enum KeepOrDrop { kKeep, kDrop };
    enum FlagDepth { kNone, kFirst, kAll };
    KeepOrDrop keepOrDrop_;
    FlagDepth daughtersDepth_, mothersDepth_;
    bool all_;
  };
}

class ICGenParticlePruner53X : public edm::EDProducer {
public:
  ICGenParticlePruner53X(const edm::ParameterSet&);
private:
  void produce(edm::Event&, const edm::EventSetup&);
  bool firstEvent_;
  edm::InputTag src_;
  int keepOrDropAll_;
  std::vector<std::string> selection_;
  std::vector<std::pair<StringCutObjectSelector<reco::GenParticle>, helper::SelectCode> > select_;
  std::vector<int> flags_;
  std::vector<size_t> indices_;
  void parse(const std::string & selection, helper::SelectCode & code, std::string & cut) const;
  void flagDaughters(const reco::GenParticle &, int); 
  void flagMothers(const reco::GenParticle &, int); 
  void recursiveFlagDaughters(size_t, const reco::GenParticleCollection &, int, std::vector<size_t> &); 
  void recursiveFlagMothers(size_t, const reco::GenParticleCollection &, int, std::vector<size_t> &); 
  void addDaughterRefs(std::vector<size_t> &, reco::GenParticle&, reco::GenParticleRefProd, const reco::GenParticleRefVector&) const;
  void addMotherRefs(std::vector<size_t> &, reco::GenParticle&, reco::GenParticleRefProd, const reco::GenParticleRefVector&) const;
};

using namespace edm;
using namespace std;
using namespace reco;

const int keep = 1, drop = -1;

void ICGenParticlePruner53X::parse(const std::string & selection, ::helper::SelectCode & code, std::string & cut) const {
  using namespace ::helper;
  size_t f =  selection.find_first_not_of(' ');
  size_t n = selection.size();
  string command;
  char c;
  for(; (c = selection[f]) != ' ' && f < n; ++f) {
    command.push_back(c);
  }
  if(command[0] == '+') {
    command.erase(0, 1);
    if(command[0] == '+') {
      command.erase(0, 1);
      code.mothersDepth_ = SelectCode::kAll;
    } else {
      code.mothersDepth_ = SelectCode::kFirst;
    }
  } else 
    code.mothersDepth_ = SelectCode::kNone;

  if(command[command.size() - 1] == '+') {
    command.erase(command.size() - 1);
    if(command[command.size()-1] == '+') {
      command.erase(command.size() - 1);
      code.daughtersDepth_ = SelectCode::kAll;
    } else {
      code.daughtersDepth_ = SelectCode::kFirst;
    }
  } else
    code.daughtersDepth_ = SelectCode::kNone;

  if(command == "keep") code.keepOrDrop_ = SelectCode::kKeep;
  else if(command == "drop") code.keepOrDrop_ = SelectCode::kDrop;
  else {
    throw Exception(errors::Configuration)
      << "invalid selection command: " << command << "\n" << endl;
  }
  for(; f < n; ++f) {
    if(selection[f] != ' ') break;
  }
  cut = string(selection, f);
  if(cut[0] == '*')
    cut = string(cut, 0, cut.find_first_of(' '));
  code.all_ = cut == "*";
}

ICGenParticlePruner53X::ICGenParticlePruner53X(const ParameterSet& cfg) :
  firstEvent_(true),
  src_(cfg.getParameter<InputTag>("src")), keepOrDropAll_(drop),
  selection_(cfg.getParameter<vector<string> >("select")) {
  using namespace ::helper;
  produces<GenParticleCollection>();
}

void ICGenParticlePruner53X::flagDaughters(const reco::GenParticle & gen, int keepOrDrop) {
  GenParticleRefVector daughters = gen.daughterRefVector();
  for(GenParticleRefVector::const_iterator i = daughters.begin(); i != daughters.end(); ++i) 
    flags_[i->key()] = keepOrDrop;
}

void ICGenParticlePruner53X::flagMothers(const reco::GenParticle & gen, int keepOrDrop) {
  GenParticleRefVector mothers = gen.motherRefVector();
  for(GenParticleRefVector::const_iterator i = mothers.begin(); i != mothers.end(); ++i) 
    flags_[i->key()] = keepOrDrop;
}

void ICGenParticlePruner53X::recursiveFlagDaughters(size_t index, const reco::GenParticleCollection & src, int keepOrDrop,
					       std::vector<size_t> & allIndices ) {
  GenParticleRefVector daughters = src[index].daughterRefVector();
  // avoid infinite recursion if the daughters are set to "this" particle.
  size_t cachedIndex = index;
  for(GenParticleRefVector::const_iterator i = daughters.begin(); i != daughters.end(); ++i) {
    index = i->key();
    // To also avoid infinite recursion if a "loop" is found in the daughter list,
    // check to make sure the index hasn't already been added. 
    if ( find( allIndices.begin(), allIndices.end(), index ) == allIndices.end() ) {
      allIndices.push_back( index );
      if ( cachedIndex != index ) {
	flags_[index] = keepOrDrop;
	recursiveFlagDaughters(index, src, keepOrDrop, allIndices);
      }
    }
  }
}

void ICGenParticlePruner53X::recursiveFlagMothers(size_t index, const reco::GenParticleCollection & src, int keepOrDrop,
					     std::vector<size_t> & allIndices ) {
  GenParticleRefVector mothers = src[index].motherRefVector();
  // avoid infinite recursion if the mothers are set to "this" particle.
  size_t cachedIndex = index;
  for(GenParticleRefVector::const_iterator i = mothers.begin(); i != mothers.end(); ++i) {
    index = i->key();
    // To also avoid infinite recursion if a "loop" is found in the daughter list,
    // check to make sure the index hasn't already been added. 
    if ( find( allIndices.begin(), allIndices.end(), index ) == allIndices.end() ) {
      allIndices.push_back( index );
      if ( cachedIndex != index ) {
	flags_[index] = keepOrDrop;
	recursiveFlagMothers(index, src, keepOrDrop, allIndices);
      }
    }
  }
}

void ICGenParticlePruner53X::produce(Event& evt, const EventSetup& es) {
  if (firstEvent_) {
    PdgEntryReplacer rep(es);
    for(vector<string>::const_iterator i = selection_.begin(); i != selection_.end(); ++i) {
      string cut;
      ::helper::SelectCode code;
      parse(*i, code, cut);
      if(code.all_) {
        if(i != selection_.begin())
          throw Exception(errors::Configuration)
            << "selections \"keep *\" and \"drop *\" can be used only as first options. Here used in position # "
            << (i - selection_.begin()) + 1 << "\n" << endl;
        switch(code.keepOrDrop_) {
        case ::helper::SelectCode::kDrop :
	  keepOrDropAll_ = drop; break;
        case ::helper::SelectCode::kKeep :
	  keepOrDropAll_ = keep;
        };
      } else {
        cut = rep.replace(cut);
        select_.push_back(make_pair(StringCutObjectSelector<GenParticle>(cut), code));
      }
    }
    firstEvent_ = false;
  }

  using namespace ::helper;
  Handle<GenParticleCollection> src;
  evt.getByLabel(src_, src);
  const size_t n = src->size();
  flags_.clear();
  flags_.resize(n, keepOrDropAll_);
  for(size_t j = 0; j < select_.size(); ++j) { 
    const pair<StringCutObjectSelector<GenParticle>, SelectCode> & sel = select_[j];
    SelectCode code = sel.second;
    const StringCutObjectSelector<GenParticle> & cut = sel.first;
    for(size_t i = 0; i < n; ++i) {
      const GenParticle & p = (*src)[i];
      if(cut(p)) {
	int keepOrDrop = keep;
	switch(code.keepOrDrop_) {
	case SelectCode::kKeep:
	  keepOrDrop = keep; break;
	case SelectCode::kDrop:
	  keepOrDrop = drop; 
	};
	flags_[i] = keepOrDrop;
	std::vector<size_t> allIndicesDa;
	std::vector<size_t> allIndicesMo;
	switch(code.daughtersDepth_) {
	case SelectCode::kAll : 
	  recursiveFlagDaughters(i, *src, keepOrDrop, allIndicesDa); break;
	case SelectCode::kFirst :
	  flagDaughters(p, keepOrDrop); break;
	case SelectCode::kNone:
	  ;
	};
	switch(code.mothersDepth_) {
	case SelectCode::kAll :
	  recursiveFlagMothers(i, *src, keepOrDrop, allIndicesMo); break;
	case SelectCode::kFirst :
	  flagMothers(p, keepOrDrop); break;
	case SelectCode::kNone:
	  ;
	};
      }
    }
  }
  indices_.clear();
  int counter = 0;
  for(size_t i = 0; i < n; ++i) {
    if(flags_[i] == keep) {
      indices_.push_back(i);
      flags_[i] = counter++;
    }
  }

  unique_ptr<GenParticleCollection> out(new GenParticleCollection);
  GenParticleRefProd outRef = evt.getRefBeforePut<GenParticleCollection>();
  out->reserve(counter);
  for(vector<size_t>::const_iterator i = indices_.begin(); i != indices_.end(); ++i) {
    size_t index = *i;
    const GenParticle & gen = (*src)[index];
    const LeafCandidate & part = gen;
    out->push_back(GenParticle(part));
    GenParticle & newGen = out->back();
    // The "daIndxs" and "moIndxs" keep a list of the keys for the mother/daughter
    // parentage/descendency. In some cases, a circular referencing is encountered,
    // which would result in an infinite loop. The list is checked to
    // avoid this. 
    vector<size_t> daIndxs;
    addDaughterRefs(daIndxs, newGen, outRef, gen.daughterRefVector());
    vector<size_t> moIndxs;
    addMotherRefs(moIndxs, newGen, outRef, gen.motherRefVector());
  }

  evt.put(std::move(out));
}


void ICGenParticlePruner53X::addDaughterRefs(vector<size_t> & daIndxs, 
					GenParticle& newGen, GenParticleRefProd outRef, 
					const GenParticleRefVector& daughters) const {
  for(GenParticleRefVector::const_iterator j = daughters.begin();
      j != daughters.end(); ++j) {
    GenParticleRef dau = *j;
    if ( find(daIndxs.begin(), daIndxs.end(), dau.key()) == daIndxs.end() ) {
      int idx = flags_[dau.key()];
      daIndxs.push_back( dau.key() );
      if(idx >= 0) {
	GenParticleRef newDau(outRef, static_cast<size_t>(idx));
	newGen.addDaughter(newDau);
      } else {
	const GenParticleRefVector daus = dau->daughterRefVector();
	if(daus.size()>0) {
	  addDaughterRefs(daIndxs, newGen, outRef, daus);
	}
      }
    }
  }
}



void ICGenParticlePruner53X::addMotherRefs(vector<size_t> & moIndxs,
				      GenParticle& newGen, GenParticleRefProd outRef, 
				      const GenParticleRefVector& mothers) const {
  for(GenParticleRefVector::const_iterator j = mothers.begin();
      j != mothers.end(); ++j) {
    GenParticleRef mom = *j;
    if ( find(moIndxs.begin(), moIndxs.end(), mom.key()) == moIndxs.end() ) {
      int idx = flags_[mom.key()];
      moIndxs.push_back( mom.key() );
      if(idx >= 0) {
	GenParticleRef newMom(outRef, static_cast<size_t>(idx));
	newGen.addMother(newMom);
      } else {
	const GenParticleRefVector moms = mom->motherRefVector();
	if(moms.size()>0)
	  addMotherRefs(moIndxs, newGen, outRef, moms);
      }
    }
  }
}

#include "FWCore/Framework/interface/MakerMacros.h"

DEFINE_FWK_MODULE(ICGenParticlePruner53X);
