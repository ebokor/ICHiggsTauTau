#ifndef ICHiggsTauTau_SuperCluster_hh
#define ICHiggsTauTau_SuperCluster_hh
#include <map>
#include <string>
#include <vector>
#include "Math/Point3D.h"
#include "Math/Point3Dfwd.h"
#include "Math/Vector4D.h"
#include "Math/Vector4Dfwd.h"
#include "Rtypes.h"
#include "UserCode/ICHiggsTauTau/interface/Candidate.hh"

namespace ic {

/**
 * @brief See documentation [here](\ref objs-supercluster)
 */
class SuperCluster {
 private:
  typedef ROOT::Math::XYZPoint Point;
  typedef ROOT::Math::PtEtaPhiEVector Vector;

 public:
  SuperCluster();
  virtual ~SuperCluster();
  virtual void Print() const;

  /// @name Properties
  /**@{*/
  /// The supercluster 3D co-ordinates
  inline Point const& point() const { return point_; }

  /// The supercluster x-coordinate
  inline double vx() const { return point_.x(); }

  /// The supercluster y-coordinate
  inline double vy() const { return point_.y(); }

  /// The supercluster z-coordinate
  inline double vz() const { return point_.z(); }

  /// Defined as \f$ \mathrm{energy}\times\sin(\theta) \f$
  inline double pt() const { return (energy_ * sin(point_.theta())); }

  /// The \f$\eta\f$ direction of the supercluster
  inline double eta() const { return (point_.eta()); }

  /// The \f$\phi\f$ direction of the supercluster
  inline double phi() const { return (point_.phi()); }

  /// Corrected supercluster energy
  inline double const& energy() const { return energy_; }

  /// Raw supercluster energy
  inline double const& raw_energy() const { return raw_energy_; }

  /// A four-momentum constructed from the pt(), eta(), phi() and energy()
  /// values
  inline Vector vector() const { return Vector(pt(), eta(), phi(), energy_); }

  /// True if the supercluster is in the EB, false otherwise
  inline bool const& is_barrel() const { return is_barrel_; }

  /// Unique identifier
  inline std::size_t id() const { return id_; }

  inline double const& etaWidth() const { return etaWidth_; }
  inline double const& phiWidth() const { return phiWidth_; }

  inline ic::Candidate const& seed_cluster() const { return seed_cluster_; }
  inline std::vector<ic::Candidate> const& clusters() const { return clusters_; }
  inline std::vector<ic::Candidate> const& ps_clusters() const { return ps_clusters_; }

  inline float const& r9() const { return r9_; }
  inline float const& r9_full5x5() const { return r9_full5x5_; }
  inline float const& sigmaIetaIeta() const { return sigmaIetaIeta_; }
  inline float const& sigmaIetaIeta_full5x5() const { return sigmaIetaIeta_full5x5_; }
  inline unsigned const& Nclusters() const { return Nclusters_; }

  /**@}*/

  /// @name Setters
  /**@{*/

  /// @copybrief point()
  inline void set_point(Point const& point) { point_ = point; }

  /// @copybrief vx()
  inline void set_vx(double const& x) { point_.SetX(x); }

  /// @copybrief vy()
  inline void set_vy(double const& y) { point_.SetY(y); }

  /// @copybrief vz()
  inline void set_vz(double const& z) { point_.SetZ(z); }

  /// @copybrief id()
  inline void set_id(std::size_t const& id) { id_ = id; }

  /// @copybrief energy()
  inline void set_energy(double const& energy) { energy_ = energy; }

  /// @copybrief raw_energy()
  inline void set_raw_energy(double const& raw_energy) {
    raw_energy_ = raw_energy;
  }

  /// @copybrief is_barrel()
  inline void set_is_barrel(bool const& is_barrel) { is_barrel_ = is_barrel; }

  inline void set_phiWidth(double const& phiWidth) {
    phiWidth_ = phiWidth;
  }

  inline void set_etaWidth(double const& etaWidth) {
    etaWidth_ = etaWidth;
  }

  inline void set_seed_cluster(ic::Candidate const& seed_cluster) {
    seed_cluster_ = seed_cluster;
  }

  inline void set_clusters(std::vector<ic::Candidate> const& clusters) {
    clusters_ = clusters;
  }

  inline void set_ps_clusters(std::vector<ic::Candidate> const& ps_clusters) {
    ps_clusters_ = ps_clusters;
  }


  inline void set_r9(float const& r9) {
    r9_ = r9;
  }

  inline void set_r9_full5x5(float const& r9_full5x5) {
    r9_full5x5_ = r9_full5x5;
  }

  inline void set_sigmaIetaIeta(float const& sigmaIetaIeta) {
    sigmaIetaIeta_ = sigmaIetaIeta;
  }

  inline void set_sigmaIetaIeta_full5x5(float const& sigmaIetaIeta_full5x5) {
    sigmaIetaIeta_full5x5_ = sigmaIetaIeta_full5x5;
  }

  inline void set_Nclusters(unsigned const& Nclusters) {
    Nclusters_ = Nclusters;
  }

  /**@}*/

 private:
  Point point_;
  std::size_t id_;
  double energy_;
  double raw_energy_;
  bool is_barrel_;
  double etaWidth_;
  double phiWidth_;
  std::vector<ic::Candidate> clusters_;
  std::vector<ic::Candidate> ps_clusters_;
  ic::Candidate seed_cluster_;
  float r9_;
  float r9_full5x5_;
  float sigmaIetaIeta_;
  float sigmaIetaIeta_full5x5_;
  unsigned Nclusters_;
 #ifndef SKIP_CINT_DICT
 public:
  ClassDef(SuperCluster, 3);
 #endif
};

typedef std::vector<ic::SuperCluster> SuperClusterCollection;
}
/** \example plugins/ICSuperClusterProducer.cc */
#endif
