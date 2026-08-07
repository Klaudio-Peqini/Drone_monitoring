# Data governance and provenance

Raw data are immutable. Processed data are derived products and may be regenerated, never substituted for raw acquisition. Every transformation should have a script/configuration and version. Use stable run IDs. Hash raw data after acquisition. Record calibration and correction versions on every processed record. Store timestamps in UTC. Do not place passwords, tokens or personally sensitive data in the repository. Back up raw data to at least two independent storage locations before deleting acquisition-device copies.
