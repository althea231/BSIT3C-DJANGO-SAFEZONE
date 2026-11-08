SAFEZONE: AN INTERACTIVE WEB AND PROGRESSIVE WEB APPLICATION FOR GOCE COMMUNITY-BASED DISASTER RESPONSE AND EVACUATION MAPPING

CONCEPT PAPER

INTRODUCTION

Background of the Project
The community of Galicia, Ilog, Negros Occidental frequently encounters severe challenges during natural calamities, particularly severe typhoons and sudden heavy flooding. During these emergency situations, affected residents struggle to identify operational evacuation centers, accessible safe travel routes, and active flood-prone hazard areas in real time.

The current landscape predominantly relies on traditional dissemination channels, such as physical public announcements, manual word-of-mouth updates, or static paper maps. These legacy methods often lead to delayed responses, widespread confusion during emergency evacuations, and highly risky route selection by fleeing residents. When cellular tower traffic spikes or infrastructure suffers damage, access to updated spatial information becomes severely restricted.


To address these critical communication and navigation gaps, an information technology solution is required. The proposed project will introduce SafeZone, an interactive web application. SafeZone will provide accessible, real-time spatial visualization and critical safety data directly to members of the Galicia community and disaster response teams. By leveraging modern web-based Geographic Information System (GIS) tools, the system will offer access to dynamic location updates, safe navigation paths, and disaster preparedness guidelines.

Statement of the Problem or Project Objectives

Main Objective
The main objective of this project is to design, develop, and evaluate SafeZone, an interactive web application designed to map evacuation centers, flood-prone paths, and emergency hazard zones for the Galicia community during typhoons and natural calamities.

Specific Technical Objectives
1.	The project will develop an interactive web interface incorporating dynamic map visualization utilizing Leaflet.js to display evacuation centers in the Galicia community, flood paths, and emergency hazard zones.
2.	The project will integrate an administrative geotagging module to pin emergency hazard zones, active shelters, and risk points using precise spatial coordinates.
3.	The project will implement a local document viewer module for rendering emergency hazard guidelines, evacuation procedures, and disaster preparedness resources via local PDF and image viewers.
4.	The project will conduct User Acceptance Testing (UAT) with residents of the Galicia community (as public viewers) and disaster management personnel (as system administrators) to evaluate system usability, reliability, and mapping accuracy.

Significance of the Project
The implementation of SafeZone will deliver direct technical and operational benefits to several key stakeholder groups:
•	Residents of the Galicia community: The web application will enable rapid, log-in free public access, to safe evacuation routes and active shelter maps during severe weather and flooding events, reducing emergency response delays and human risk.

•	Local Government Units (LGUs) and Disaster Risk Reduction Management (DRRM) Officers: The platform will provide an accessible digital management tool to communicate real-time shelter statuses, hazard zones, and evacuation advisories efficiently to the public.

•	Emergency Responders: The web application will assist rescue teams in effective route planning and enhanced spatial awareness when conducting emergency relief and rescue operations in compromised areas.

•	Future Researchers and IT Students: The proposed platform will serve as an academic and practical reference framework for future web-based spatial applications and disaster risk management software architectures.

Alignment with Institutional Research Agenda and Sustainable Development Goals
Institutional Research Agenda Alignment
This project directly aligns with the Institutional IT and Governance Research priority. By implementing open-source web-based GIS tools, the project directly addresses public safety challenges and supports digital governance solutions aimed at enhancing disaster resiliency in the Galicia community.
Sustainable Development Goal (SDG) Alignment
●	SDG 11: Sustainable Cities and Communities: SafeZone will strengthen Galicia community disaster resilience by providing accessible digital spatial mapping, emergency safety guidance, and real-time navigation toward safety hubs.
●	SDG 13: Climate Action: The platform will enhance climate change mitigation and emergency response readiness through proactive mapping of flood-prone areas, hazard zones, and structured evacuation procedures.

SCOPE AND LIMITATIONS
System Scope & Technical Architecture
The SafeZone platform will focus on providing spatial awareness and emergency document access for disaster management within the Galicia community. The technical scope and system architecture are summarized in the structured breakdown below:

Dimension	Project Specification & Capabilities
Core Modules	• Interactive Hazard & Evacuation Map Module: Renders dynamic maps with overlays for evacuation sites, hazard zones, and safe travel paths.
• Geotagging & Coordinate Mapping Module: Enables positioning and pinning of active shelters, hazards, and risk points via latitude and longitude coordinates.
• Local PDF/Image Resource Viewer: Renders downloadable disaster preparedness manuals, emergency checklists, and evacuation guides offline.
Technology Stack	• Frontend: HTML5, CSS3, JavaScript (ES6+)
• Mapping Library: Leaflet.js. 
• Storage: LocalStorage / IndexedDB •Document Rendering: Local PDF/Image rendering scripts
Target Users	• Residents of the Galicia community 
•LGU Disaster Risk Reduction Officers •Emergency Response and Rescue Teams

System Limitations
To ensure project feasibility within the designated capstone development timeline, the following limitations are explicitly defined:

1.	Automated Hardware Sensor Integration: The system will focus exclusively on Galicia community-level spatial mapping and manual or semi-automated status updating. Real-time automated hardware sensor integration (such as ultrasonic water level sensors or river gauge telemetry) is excluded from the current scope.
2.	Live Satellite & External Weather Feeds: Live-feed satellite imagery integration and automated real-time weather forecasting API synchronization will not be developed in this phase.
3.	Future Recommendations: Automated IoT hardware integrations, satellite feed layers, and automated meteorological API connections will be formally recommended for future development iterations.

