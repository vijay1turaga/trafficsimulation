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

int main (int argc, char *argv[])
{
  uint32_t nNodes = 50; // Number of vehicles
  double simulationTime = 60.0; // seconds
  double range = 200.0; // communication range in meters

  CommandLine cmd;
  cmd.AddValue ("nNodes", "Number of nodes", nNodes);
  cmd.AddValue ("simulationTime", "Simulation time", simulationTime);
  cmd.AddValue ("range", "Communication range", range);
  cmd.Parse (argc, argv);

  // Create nodes
  NodeContainer nodes;
  nodes.Create (nNodes);

  // Mobility model - RandomWaypoint for VANET
  MobilityHelper mobility;
  mobility.SetMobilityModel ("ns3::RandomWaypointMobilityModel",
                             "Speed", StringValue ("ns3::UniformRandomVariable[Min=10|Max=30]"),
                             "Pause", StringValue ("ns3::ConstantRandomVariable[Constant=0.0]"),
                             "PositionAllocator", StringValue ("ns3::RandomRectanglePositionAllocator"));
  mobility.SetPositionAllocator ("ns3::RandomRectanglePositionAllocator",
                                 "X", StringValue ("ns3::UniformRandomVariable[Min=0|Max=1000]"),
                                 "Y", StringValue ("ns3::UniformRandomVariable[Min=0|Max=1000]"));
  mobility.Install (nodes);

  // WAVE setup
  YansWifiChannelHelper waveChannel = YansWifiChannelHelper::Default ();
  YansWifiPhyHelper wavePhy = YansWifiPhyHelper::Default ();
  wavePhy.SetChannel (waveChannel.Create ());
  wavePhy.Set ("TxPowerStart", DoubleValue (20.0));
  wavePhy.Set ("TxPowerEnd", DoubleValue (20.0));
  wavePhy.Set ("TxPowerLevels", UintegerValue (1));
  wavePhy.Set ("TxGain", DoubleValue (1.0));
  wavePhy.Set ("RxGain", DoubleValue (1.0));
  wavePhy.Set ("RxNoiseFigure", DoubleValue (7.0));

  QosWaveMacHelper waveMac = QosWaveMacHelper::Default ();
  WaveHelper waveHelper = WaveHelper::Default ();
  waveHelper.SetRemoteStationManager ("ns3::ConstantRateWifiManager",
                                      "DataMode", StringValue ("OfdmRate6MbpsBW10MHz"),
                                      "ControlMode", StringValue ("OfdmRate6MbpsBW10MHz"));

  NetDeviceContainer waveDevices = waveHelper.Install (wavePhy, waveMac, nodes);

  // Internet stack
  InternetStackHelper stack;
  stack.Install (nodes);

  // Assign IP addresses
  Ipv4AddressHelper address;
  address.SetBase ("10.1.1.0", "255.255.255.0");
  Ipv4InterfaceContainer interfaces = address.Assign (waveDevices);

  // Applications - V2V communication
  uint16_t port = 9;
  for (uint32_t i = 0; i < nNodes; ++i)
    {
      Address sinkAddress (InetSocketAddress (interfaces.GetAddress (i), port));
      PacketSinkHelper packetSinkHelper ("ns3::UdpSocketFactory", sinkAddress);
      ApplicationContainer sinkApps = packetSinkHelper.Install (nodes.Get (i));
      sinkApps.Start (Seconds (0.0));
      sinkApps.Stop (Seconds (simulationTime));

      for (uint32_t j = 0; j < nNodes; ++j)
        {
          if (i != j)
            {
              Ptr<VanetApp> app = CreateObject<VanetApp> ();
              app->Setup (Socket::CreateSocket (nodes.Get (j), UdpSocketFactory::GetTypeId ()),
                          sinkAddress, 512, 1000000, DataRate ("1Mbps"));
              nodes.Get (j)->AddApplication (app);
              app->SetStartTime (Seconds (1.0 + j * 0.1));
              app->SetStopTime (Seconds (simulationTime));
            }
        }
    }

  // Flow monitor
  FlowMonitorHelper flowmon;
  Ptr<FlowMonitor> monitor = flowmon.InstallAll ();

  // Output mobility trace
  AsciiTraceHelper ascii;
  MobilityHelper::EnableAsciiAll (ascii.CreateFileStream ("mobility-trace.tr"));

  Simulator::Stop (Seconds (simulationTime));
  Simulator::Run ();

  // Flow monitor stats
  monitor->CheckForLostPackets ();
  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier> (flowmon.GetClassifier ());
  std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats ();

  std::ofstream qosFile ("qos_metrics.csv");
  qosFile << "FlowId,TxPackets,RxPackets,TxBytes,RxBytes,PDR,Latency\n";
  for (std::map<FlowId, FlowMonitor::FlowStats>::const_iterator i = stats.begin (); i != stats.end (); ++i)
    {
      double pdr = (double)i->second.rxPackets / i->second.txPackets;
      double latency = i->second.delaySum.GetSeconds () / i->second.rxPackets;
      qosFile << i->first << "," << i->second.txPackets << "," << i->second.rxPackets << ","
              << i->second.txBytes << "," << i->second.rxBytes << "," << pdr << "," << latency << "\n";
    }
  qosFile.close ();

  Simulator::Destroy ();
  return 0;
}