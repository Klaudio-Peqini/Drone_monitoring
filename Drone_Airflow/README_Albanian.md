# Rrjedhja e ajrit 3D — vendosja e stacionit monitorues

Kjo paketë Python studion pozicionin e një stacioni monitorues brenda **1 m nga
qendra e DJI Matrice 350 RTK**, në çdo drejtim. Qëllimi është marrja e një mostre
sa më përfaqësuese të ajrit të patrazuar të mjedisit, edhe në prani të erës.
Nuk kërkohet ndërfaqe grafike, Jupyter, OpenFOAM, FFmpeg ose GPU.

**Statusi shkencor:** përmasat e stacionit, disa hollësi të gjeometrisë së dronit,
momenti i rotorëve dhe rezistenca aerodinamike përmbajnë supozime të deklaruara.
Nuk janë dhënë matje për kalibrimin eksperimental të gjurmës së Matrice ose
për gjeometrinë reale të stacionit. Rezultatet janë **vlerësim numerik paraprak**,
jo miratim i një montimi fizik. Pozicioni me renditjen më të mirë mund t'i
shkelë përsëri tolerancat.

Shpjegimet e plota të ekuacioneve dhe metodave janë në
`docs/placement_physics.md`; rezultatet e ekzekutimit të pranuar janë në
`docs/study_results.md`. Udhëzuesi anglisht është `README.md`.

## 1. Instalimi dhe kontrolli i parë

Shpaketoni të gjithë arkivin. Hapni terminalin brenda dosjes `Drone_Airflow_3D`,
ku ndodhen `flow3d.py`, `requirements.txt`, `cases/` dhe `drone_airflow3d/`.
Kërkohet Python 3.10 ose më i ri.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python flow3d.py --help
python -m unittest discover -s tests -v
```

Nëse Ubuntu nuk përmban venv, instaloni paketën përkatëse `python3-venv` ose
kërkojini administratorit. Mund të aktivizoni edhe mjedisin tuaj ekzistues
`.cfd_venv`. Kur është aktiv edhe Conda, përdorni `which python` për të parë
interpretuesin që po përdoret realisht.

Në Windows përdorni `py -m venv .venv` dhe aktivizojeni nga PowerShell me
`.venv\Scripts\Activate.ps1`. Komandat e tjera Python mbeten të njëjta.
Komandat shkruhen në terminal, jo pas shenjës `>>>`. Mos ekzekutoni skedarë
brenda ZIP-it pa e shpaketuar. Pas instalimit, ekzekutimi nuk kërkon internet.

## 2. Shihni rezultatet e përfshira pa rillogaritur

Studimi i përfshirë ndodhet në `examples/matrice_placement/`.

| Skedari/dosja | Përmbajtja |
|---|---|
| `placement_report.json` | Kandidati më i mirë për provë, kriteret dhe kufijtë e vlefshmërisë. |
| `placement_map.csv` | Pozicionet e mundshme dhe metrikat më të këqija të të gjithë skenarëve. |
| `placement_map.npz` | Harta numerike, pikët dhe maskat e kualifikimit. |
| `installed_report.json` | Kontrollet me stacionin, mbajtësen dhe masën jashtë qendrës. |
| `sensitivity_report.json` | Ndikimi i rrjetës, hapit kohor, domain-it dhe gjerësisë së forcës. |
| `verification_report.json` | Kontrollet numerike dhe kontrollet e GIF-eve. |
| `animations/` | Shtatë GIF-et, PNG-të përfundimtare dhe metadatat. |
| `scenarios/`, `sensitivity/`, `installed/` | Konfigurimet dhe rezultatet e rasteve individuale. |

Për shembull, në Ubuntu:

```bash
xdg-open examples/matrice_placement/animations/placement_3d.gif
xdg-open examples/matrice_placement/animations/velocity_3d.gif
```

Lexoni `passes_screening` dhe `screened_acceptable_count`, jo vetëm renditjen.
Një bashkësi bosh pozicionesh që kalojnë kriteret do të thotë se modeli nuk
ka gjetur pozicion të përshtatshëm nën tolerancat e zgjedhura. `approved_count`
mbetet zero sepse mungon validimi fizik; kjo nuk provon se çdo montim real
brenda 1 m është i papërshtatshëm.

## 3. Ekzekutoni studimin e plotë

```bash
python flow3d.py study \
  --case cases/matrice_placement.json \
  --out results/my_placement_study \
  --jobs 4 --threads 1 --installed-position -0.3 -0.3 0.9
```

Komanda llogarit ndjeshmëritë numerike, skenarët e erës/ngarkesës, hartën e
pozicioneve, kandidatët me stacion të instaluar dhe animimet. Me `--no-render`
llogariten vetëm fushat dhe statistikat. Nëse keni më pak CPU, përdorni
`--jobs 1 --threads 1`. Studimi mund të kërkojë minuta deri në dhjetëra minuta
ose më shumë, sipas makinës dhe parametrave; eksportimi grafik kërkon kohë më
vete.

Ndjeshmëria vlerësohet lokalisht për çdo kandidat. Një pozicion ku ndryshimi i
rrjetës, gjerësisë së forcës ose dritares së mesatarizimit është tepër i madh
mbetet i pakualifikuar. Pikët e ulëta nuk fshehin një kontroll të dështuar.

Pas një ndërprerjeje, përsëritni të njëjtën komandë në të njëjtën dosje dalëse.
Rastet e përfunduara me parametra dhe koordinata identike ripërdoren. Rasti që
u ndërpre rillogaritet nga fillimi. Kjo është rinisje në nivel rasti, jo ruajtje
e gjendjes së çdo hapi kohor. Nëse ndryshoni hyrjet, përdorni dosje të re.
Dosjet e tjera jo bosh mbrohen nga mbishkrimi.

Për një provë të shkurtër instalimi, kopjoni JSON-in me emër tjetër dhe
vendosni cells=24, force_width_m=0.28, duration_s=0.08, average_from_s=0.04,
frames=5, spacing_m=0.25, installed_candidates=1 dhe vetëm skenarin pa erë.
Përdoreni fillimisht me `--no-render`. Kjo kontrollon ekzekutimin, jo saktësinë
fizike të vendosjes së stacionit.

## 4. Krijoni dhe ndryshoni GIF-et

Kuadrot e rastit të zgjedhur ruhen, prandaj mund t'i rigjeneroni animimet pa
përsëritur zgjidhjen CFD:

```bash
python flow3d.py render-study \
  --input examples/matrice_placement \
  --styles all --fps 6 --dpi 90
```

Për një studim të ri përdorni dosjen tuaj `results/my_placement_study`. Për
vetëm disa fusha dhe një kamerë që lëviz:

```bash
python flow3d.py render-study --input results/my_placement_study --styles pressure vorticity concentration --fps 6 --orbit
```

| Stili | Skedari dhe kuptimi |
|---|---|
| `velocity` | `velocity_3d.gif`: vektorët e shpejtësisë në 3D. |
| `streamlines` | `streamlines_3d.gif`: vijat tangjente me fushën në çdo çast. |
| `particles` | `particles_3d.gif`: gjurmues pasivë dhe pjesë të trajektoreve. |
| `pressure` | `pressure_3d.gif`: izosipërfaqe të presionit relativ. |
| `vorticity` | `vorticity_3d.gif`: izosipërfaqe të modulit të vorticitetit të filtruar. |
| `concentration` | `concentration_3d.gif`: izosipërfaqe të përqendrimit të gazit të transportuar. |
| `placement` | `placement_3d.gif`: pamje rrotulluese e hartës së të gjithë skenarëve. |

Këto janë skena tredimensionale, jo prerje planare të vendosura njëra mbi
tjetrën. Ngjyrat përdorin kufij të pandryshuar gjatë një animimi. Për presionin
përdoret shkallë logaritmike simetrike, që i bën të dukshme edhe ndryshimet e
vogla duke ruajtur vlerat reale dhe njësitë. Vorticiteti nuk përfaqëson vorbulla
fizike të zgjidhura në majat e helikave.

Droni, disqet e rotorëve, stacioni dhe mbajtësja shërbejnë si kontekst i
modelit. Sfera gri shënon shtrirjen 1 m. Figura tregon një pjesë të domain-it
për lexueshmëri, ndërsa simulimi kryhet në domain më të madh.

Animimet e fushave shënojnë kohën fizike. Harta e vendosjes është një rezultat
statik i vrojtuar nga kamerë rrotulluese; kuadrot e saj nuk janë hapa fizikë
simulimi. E gjelbra shënon vetëm kalimin e kritereve paraprake, jo miratim
fizik. Ylli i kuq shënon kandidatin më të mirë për provë.

Ulni `--fps` për shfaqje më të ngadaltë. Ky argument nuk ndryshon fizikën.
GIF përdor vonesa në shumëfisha 10 ms; koha reale e shfaqjes ruhet në raport.
`--dpi` ndryshon madhësinë e figurës, jo rrjetën CFD. `--orbit` ndryshon
këndvështrimin. Rigjenerimi zëvendëson GIF-et/PNG-të me emrat përkatës.

## 5. Mos ngatërroni katër paraqitje transporti

* Vijat e rrjedhjes tregojnë drejtimin në një çast; nuk janë histori grimcash.
* Gjurmuesit pasivë ndjekin fushën e ruajtur të shpejtësisë. Kur dalin nga
  vëllimi, rikthehen te pikat fillestare dhe gjurma ndërpritet. Dendësia e tyre
  grafike nuk është përqendrim.
* Përqendrimi i gazit zgjidh një ekuacion të veçantë konservativ
  adveksioni–difuzioni, përfshirë përzierjen nënrrjetore.
* Aerosolet me inerci ndjekin një model tjetër me rezistencë, korrigjim të
  rrëshqitjes dhe gravitet. Eksportimi i gjurmuesve ruan edhe
  `aerosol_trajectories.npz` dhe `aerosol_report.json` për madhësitë e zgjedhura.
  Këto nuk japin përqendrimin PM, efikasitetin e aspirimit ose depozitimin.

## 6. Parametrat fizikë dhe kohëzgjatja

Të gjitha njësitë janë SI; përqendrimi jepet shprehimisht në µg/m³.

| Seksioni JSON | Parametrat kryesorë |
|---|---|
| `numerics` | Rrjeta, domain-i, koha, mesatarizimi, kuadrot, CFL, gjerësia e forcës, modeli SGS dhe shtresa kufitare zbutëse. |
| `air` | Dendësia, viskoziteti, shpejtësia e zërit dhe presioni referencë. |
| `aircraft` | Përmasat e publikuara, supozimet e motorëve, masa, rezistenca dhe kalibrimi. |
| `station` | Masa shtesë, përmasat, mbajtësja, hyrja e mostrës dhe hapësirat e lira. |
| `gas` | Përqendrimi i mjedisit, gradienti, difuziviteti dhe numri Schmidt turbulent. |
| `aerosols` | Diametrat, dendësia, viskoziteti i ajrit dhe rruga e lirë mesatare. |
| `search` | Rrezja e kërkimit, largësia midis kandidatëve dhe numri i provave të instaluara. |
| `criteria` | Tolerancat fizike dhe numerike. |
| `scenarios` | Ngarkesa shtesë dhe vektorët horizontalë të erës. |

Për 5 sekonda simulim dhe mesatarizim të 2 sekondave të fundit vendosni
`duration_s=5` dhe `average_from_s=3`. Më shumë kuadro ruajnë më mirë historinë
kohore dhe kërkojnë më shumë hapësirë. Ndryshimi i FPS nuk e zgjat kohën fizike.

Shtatë rastet fillestare përfshijnë qetësi në dy ngarkesa, ±3 m/s përgjatë të
dy boshteve horizontale në ngarkesën e vogël dhe +5 m/s në ngarkesën më të
madhe. Ky është një grup i fundëm kushtesh, jo çdo situatë atmosferike.
Pjerrësia dhe ngarkesat e rotorëve llogariten me ekuilibër algjebrik. Nuk
simulohen shkulmet e erës ose kontrollori real i DJI-së.

Kufiri 1 m zbatohet për qendrën e stacionit; hyrja mund të jetë më larg për
shkak të zhvendosjes së saj. Të dy koordinatat raportohen. Rritja e dendësisë
së kandidatëve nuk rafinon rrjedhjen ose vetë hyrjen centimetrike.
Masa bazë 6.47 kg përfshin konfigurimin referencë me gimbal; përshtateni nëse
stacioni e zëvendëson atë pajisje.

## 7. Tolerancat dhe kuptimi i kualifikimit

Tolerancat fillestare janë kërkesa ilustruese, jo specifikime të sensorit:

| Madhësia | Kufiri |
|---|---:|
| Shpejtësia mesatare shtesë ndaj mjedisit | 0.20 m/s |
| RMS i luhatjeve të zgjidhura | 0.15 m/s |
| Moduli i presionit relativ mesatar | 2 Pa |
| Gabimi absolut mesatar i përqendrimit | 2 µg/m³ |
| Fraksioni i rrjedhjes kundër erës, kur zbatohet | 0.05 |
| Ndryshimi midis mesatareve të dy gjysmave kohore | 0.08 m/s |

Pikët përcaktohen nga raporti më i keq madhësi/tolerancë, mbi të gjithë
skenarët. Vlera <=1 është kusht i nevojshëm; duhen kaluar edhe kontrollet e
ndjeshmërisë dhe mesatarizimit. Kjo shmang fshehjen e një drejtimi problematik
të erës pas një mesatareje të mirë.

Rrjedhja kundër erës është vetëm tregues paralajmërues, jo provë e plotë e
riqarkullimit. Në ajër të qetë ky tregues nuk zbatohet. RMS nuk përfshin
luhatjet nënrrjetore ose turbulencën atmosferike të pazgjidhur.
Maska `approved` mbetet false në këtë version. Një kurbë forcash e matur,
ose ndryshimi i flamurit `experimental_calibration_required`, nuk zëvendëson
validimin fizik të hyrjes së instaluar.

## 8. Kalibrimi dhe validimi me matje

Plotësoni modelin bosh `calibration/rotor_load_measurements_template.csv` me të
paktën tre pika të matura realisht: RPM, forcë në N dhe moment në N m.

```bash
python flow3d.py calibrate --csv calibration/my_measurements.csv --out calibration/my_rotor_fit.json
```

Vendosni rrugën e rezultatit te `aircraft.load_calibration` në një kopje të
konfigurimit. Rrugët relative interpretohen nga dosja ku nisni komandën.
Përshtatja jep CT, CQ, intervalin RPM, mbetjet dhe Q/T. Ngarkesa përcaktohet
përsëri nga ekuilibri; nuk nxirret historia RPM e kontrollorit vetëm nga masa.
Ndikimi i erës dhe forma e gjurmës kërkojnë kalibrim tjetër. Skedarët model
nuk përmbajnë matje të shpikura.

Për kontroll të pavarur plotësoni `calibration/heldout_airflow_template.csv` me
të paktën gjashtë matje. Pozicionet e qendrës së stacionit janë në sistemin e
dronit dhe përputhen me hartën. Shpejtësitë e matura janë mesatare në sistemin
global, në hyrjen përkatëse dhe në kushtet e të njëjtit skenar.

```bash
python flow3d.py validate-measurements --input results/my_placement_study --csv calibration/heldout_airflow.csv --out results/heldout_validation.json --max-error 0.15
```

Kjo komandë kontrollon fushën bazë pa stacion të instaluar. Mos përdorni të
njëjtat të dhëna për përshtatje dhe validim të pavarur. Kontrolli nuk miraton
hyrjen e instaluar ose matjet PM. Protokolli vijues është në
`docs/measurement_protocol.md`.

## 9. Verifikimi, CPU-të dhe memoria

```bash
python -m unittest discover -s tests -v
python flow3d.py verify-study --input examples/matrice_placement
python verify_release.py
```

Testet kontrollojnë ekuilibrin, projektimin pa divergjencë, presionin,
konservimin e gazit, interpolimin, vorticitetin, grimcat, izosipërfaqet,
statistikat e hyrjes dhe mbrojtjen e daljeve. Ndjeshmëritë numerike ruhen si
rezultate më vete; nuk janë intervale statistikore besimi ose provë e rendit
asimptotik të konvergjencës.

`study` me kod daljeje 0 do të thotë se llogaritja përfundoi, jo që u gjet një
pozicion i pranueshëm. `verify-study` jep 1 kur dështon një kontroll numerik.
Gabimet e hyrjes ose mjedisit japin 2. Lexoni gjithmonë raportin e vendosjes.

`--jobs` ekzekuton raste të pavarura në procese të ndryshme. `--threads`
përcakton workers FFT të presionit për proces. Prodhimi i tyre duhet të jetë
brenda buxhetit CPU. Momenti, gazi dhe vizatimi nuk bëhen automatikisht
Numba-parallel. Kufizohen grupet BLAS/OpenMP për të shmangur mbingarkimin.

Kontrollohen affinity, kuotat cgroup-v2 dhe disa kufij Slurm/HTCondor.
`CFD_CPU_LIMIT` mund të vendosë kufi më të vogël. Nuk ka GPU ose MPI në këtë
version; kërkoni një proces drejtues me disa CPU, jo disa ranks MPI.

Çdo worker mban fushat dhe gradientët në RAM. Filloni me pak procese.
`snapshot_stride` ul madhësinë e kuadrove grafikë; statistikat e kandidatëve
përdorin rrjetën numerike origjinale. Kufiri paraprak i memories është vetëm
vlerësim. Shembujt në `batch/` kërkojnë Python me varësitë e instaluara dhe
rrugët/alokimet e përshtatura për sitin. Nuk janë dërguar punë në CERN ose në
cluster të jashtëm.

## 10. Ruajtja dhe përputhshmëria

Ruhet një pemë burimore dhe një ZIP aktual. Daljet e vjetra të tepërta,
cache-t dhe pamjet e përkohshme përjashtohen. Raportet dhe statistikat e
rasteve të ndryshme ruhen sepse janë evidencë shkencore.

Fushat grafikë ruhen float32 me formë `(time,nx,ny,nz)` dhe koordinata globale.
Zgjidhësi dhe statistikat përdorin float64. Këto kuadro nuk janë checkpoint
për rinisje të saktë të hapit kohor. Harta e vendosjes përdor koordinata të
trupit të dronit. Pas ndryshimit të algoritmit numerik përdorni dosje të re;
krahasimi i konfigurimeve nuk e zëvendëson kontrollin e versionit burimor.

Komandat e hershme mbeten të vlefshme:

```bash
python flow3d.py run --case cases/single_rotor.json --out results/legacy_single --style both
python flow3d.py render --input results/legacy_single --style particles --fps 6 --overwrite
```

Ato përdorin modelin e mëparshëm mësimor me vija forcash dhe nuk janë raste
Matrice. Tre modulet burimore origjinale ruhen të pandryshuara; prejardhja dhe
hash-et gjenden në `docs/source_provenance.json`.

Një provë e shkurtër e nisjes nuk mund të kualifikojë montimin: mesatarizimi duhet të fillojë pas rritjes së ngarkesës dhe të përfshijë të paktën pesë kohë nominale kalimi të rotorit. Ky është vetëm kontroll minimal. Ngjyrat e hartës përdorin shkallë logaritmike, me kufirin e kritereve te vlera 1.

Për të riprodhuar të 38 rastet e përfshira, shtoni `--installed-position -0.3 -0.3 0.9`. Pa të, lista automatike me dy pozicione kërkon 31 raste dhe jep të njëjtën hartë bazë. Argumenti `--installed-position X Y Z` mund të përsëritet për prova të tjera të realizueshme.
