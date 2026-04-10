#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/mobility-module.h"
#include "ns3/wifi-module.h"
#include "ns3/wave-module.h"
#include "ns3/internet-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"
#include <vector>
#include <fstream>
#include <sstream>
#include <string>
#include <algorithm>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("VanetSimulation");

class VanetApp : public Application
{
public:
  VanetApp ();
  virtual ~VanetApp ();
  void Setup (Ptr<Socket> socket, Address address, uint32_t packetSize, uint32_t nPackets, DataRate dataRate);

private:
  virtual void StartApplication (void);
  virtual void StopApplication (void);
  void ScheduleTx (void);
  void SendPacket (void);

  Ptr<Socket>     m_socket;
  Address         m_peer;
  uint32_t        m_packetSize;
  uint32_t        m_nPackets;
  DataRate        m_dataRate;
  EventId         m_sendEvent;
  bool            m_running;
  uint32_t        m_packetsSent;
};

VanetApp::VanetApp ()
  : m_socket (0),
    m_peer (),
    m_packetSize (0),
    m_nPackets (0),
    m_dataRate (0),
    m_sendEvent (),
    m_running (false),
    m_packetsSent (0)
{
}

VanetApp::~VanetApp ()
{
  m_socket = 0;
}

void
VanetApp::Setup (Ptr<Socket> socket, Address address, uint32_t packetSize, uint32_t nPackets, DataRate dataRate)
{
  m_socket = socket;
  m_peer = address;
  m_packetSize = packetSize;
  m_nPackets = nPackets;
  m_dataRate = dataRate;
}

void
VanetApp::StartApplication (void)
{
  m_running = true;
  m_packetsSent = 0;
  m_socket->Bind ();
  m_socket->Connect (m_peer);
  SendPacket ();
}

void
VanetApp::StopApplication (void)
{
  m_running = false;
  if (m_sendEvent.IsRunning ())
    {
      Simulator::Cancel (m_sendEvent);
    }
  if (m_socket)
    {
      m_socket->Close ();
    }
}

void
VanetApp::SendPacket (void)
{
  Ptr<Packet> packet = Create<Packet> (m_packetSize);
  m_socket->Send (packet);
  if (++m_packetsSent < m_nPackets)
    {
      ScheduleTx ();
    }
}

void
VanetApp::ScheduleTx (void)
{
  if (m_running)
    {
      Time tNext (Seconds (m_packetSize * 8 / static_cast<double> (m_dataRate.GetBitRate ())));
      m_sendEvent = Simulator::Schedule (tNext, &VanetApp::SendPacket, this);
    }
}

struct MobilityUpdate {
  double time;
  uint32_t nodeIndex;
  double x;
  double y;
};

std::vector<MobilityUpdate> ParseMobilityTrace(const std::string& filename) {
  std::vector<MobilityUpdate> updates;
  std::ifstream file(filename);
  if (!file.is_open()) {
    std::cout << "Unable to open mobility trace: " << filename << std::endl;
    return updates;
  }

  std::string line;
  std::getline(file, line); // header
  while (std::getline(file, line)) {
    if (line.empty()) {
      continue;
    }
    std::stringstream ss(line);
    std::string token;
    double time = 0.0;
    uint32_t nodeIndex = 0;
    double x = 0.0;
    double y = 0.0;

    std::getline(ss, token, ',');
    time = std::stod(token);
    std::getline(ss, token, ','); // vehicle_id
    std::getline(ss, token, ',');
    nodeIndex = static_cast<uint32_t>(std::stoul(token));
    std::getline(ss, token, ','); // speed
    std::getline(ss, token, ','); // acceleration
    std::getline(ss, token, ',');
    x = std::stod(token);
    std::getline(ss, token, ',');
    y = std::stod(token);

    updates.push_back({time, nodeIndex, x, y});
  }

  std::sort(updates.begin(), updates.end(), [] (const MobilityUpdate& a, const MobilityUpdate& b) {
    return a.time < b.time;
  });
  return updates;
}

void SetNodePosition(Ptr<Node> node, const Vector& position) {
  Ptr<ConstantPositionMobilityModel> mobility = node->GetObject<ConstantPositionMobilityModel>();
  if (mobility) {
    mobility->SetPosition(position);
  }
}

uint32_t GetNodeIndexByAddress(const Ipv4InterfaceContainer& interfaces, const Ipv4Address& address) {
  for (uint32_t i = 0; i < interfaces.GetN(); ++i) {
    if (interfaces.GetAddress(i) == address) {
      return i;
    }
  }
  return 0;
}

int main(int argc, char *argv[]) {
  uint32_t nNodes = 50;
  double simulationTime = 60.0;
  double range = 200.0;

  CommandLine cmd;
  cmd.AddValue("nNodes", "Number of nodes", nNodes);
  cmd.AddValue("simulationTime", "Simulation time", simulationTime);
  cmd.AddValue("range", "Communication range", range);
  cmd.Parse(argc, argv);

  std::string mobilityFile = "../data/sumo_mobility_trace.csv";
  auto mobilityUpdates = ParseMobilityTrace(mobilityFile);
  if (!mobilityUpdates.empty()) {
    simulationTime = std::max(simulationTime, mobilityUpdates.back().time + 1.0);
  }

  NodeContainer nodes;
  nodes.Create(nNodes);

  MobilityHelper mobility;
  mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
  mobility.Install(nodes);

  for (const auto& update : mobilityUpdates) {
    if (update.nodeIndex < nodes.GetN()) {
      Simulator::Schedule(Seconds(update.time), &SetNodePosition, nodes.Get(update.nodeIndex), Vector(update.x, update.y, 0.0));
    }
  }

  YansWifiChannelHelper waveChannel = YansWifiChannelHelper::Default();
  YansWifiPhyHelper wavePhy = YansWifiPhyHelper::Default();
  wavePhy.SetChannel(waveChannel.Create());
  wavePhy.Set("TxPowerStart", DoubleValue(20.0));
  wavePhy.Set("TxPowerEnd", DoubleValue(20.0));
  wavePhy.Set("TxPowerLevels", UintegerValue(1));
  wavePhy.Set("TxGain", DoubleValue(1.0));
  wavePhy.Set("RxGain", DoubleValue(1.0));
  wavePhy.Set("RxNoiseFigure", DoubleValue(7.0));

  QosWaveMacHelper waveMac = QosWaveMacHelper::Default();
  WaveHelper waveHelper = WaveHelper::Default();
  waveHelper.SetRemoteStationManager("ns3::ConstantRateWifiManager",
                                      "DataMode", StringValue("OfdmRate6MbpsBW10MHz"),
                                      "ControlMode", StringValue("OfdmRate6MbpsBW10MHz"));

  NetDeviceContainer waveDevices = waveHelper.Install(wavePhy, waveMac, nodes);

  InternetStackHelper stack;
  stack.Install(nodes);

  Ipv4AddressHelper address;
  address.SetBase("10.1.1.0", "255.255.255.0");
  Ipv4InterfaceContainer interfaces = address.Assign(waveDevices);

  uint16_t port = 9;
  for (uint32_t i = 0; i < nNodes; ++i) {
    Address sinkAddress(InetSocketAddress(interfaces.GetAddress(i), port));
    PacketSinkHelper packetSinkHelper("ns3::UdpSocketFactory", sinkAddress);
    ApplicationContainer sinkApps = packetSinkHelper.Install(nodes.Get(i));
    sinkApps.Start(Seconds(0.0));
    sinkApps.Stop(Seconds(simulationTime));

    for (uint32_t j = 0; j < nNodes; ++j) {
      if (i != j) {
        Ptr<VanetApp> app = CreateObject<VanetApp>();
        app->Setup(Socket::CreateSocket(nodes.Get(j), UdpSocketFactory::GetTypeId()),
                   sinkAddress, 512, 1000000, DataRate("1Mbps"));
        nodes.Get(j)->AddApplication(app);
        app->SetStartTime(Seconds(1.0 + j * 0.1));
        app->SetStopTime(Seconds(simulationTime));
      }
    }
  }

  FlowMonitorHelper flowmon;
  Ptr<FlowMonitor> monitor = flowmon.InstallAll();

  Simulator::Stop(Seconds(simulationTime));
  Simulator::Run();

  monitor->CheckForLostPackets();
  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowmon.GetClassifier());
  std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();

  std::ofstream qosFile("../data/qos_metrics.csv");
  qosFile << "time,source_node,dest_node,TxPackets,RxPackets,TxBytes,RxBytes,PDR,Latency\n";
  for (const auto& kv : stats) {
    FlowId flowId = kv.first;
    const FlowMonitor::FlowStats& flowStats = kv.second;
    Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(flowId);
    uint32_t sourceNode = GetNodeIndexByAddress(interfaces, t.sourceAddress);
    uint32_t destNode = GetNodeIndexByAddress(interfaces, t.destinationAddress);

    double pdr = flowStats.txPackets > 0 ? static_cast<double>(flowStats.rxPackets) / flowStats.txPackets : 0.0;
    double latency = flowStats.rxPackets > 0 ? flowStats.delaySum.GetSeconds() / flowStats.rxPackets : 0.0;
    qosFile << simulationTime << "," << sourceNode << "," << destNode << ","
            << flowStats.txPackets << "," << flowStats.rxPackets << ","
            << flowStats.txBytes << "," << flowStats.rxBytes << ","
            << pdr << "," << latency << "\n";
  }
  qosFile.close();

  Simulator::Destroy();
  return 0;
}
