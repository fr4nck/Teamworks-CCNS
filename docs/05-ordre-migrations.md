# Ordre des premières migrations

Ces migrations posent le **socle du cœur Teamworks-CCNS**.

Ordre :
1. `001_create_people.sql`
2. `002_create_legal_profiles.sql`
3. `003_create_contract_types.sql`
4. `004_create_employment_regimes.sql`
5. `005_create_time_organizations.sql`
6. `006_create_contracts.sql`
7. `007_create_ccns_classifications.sql`
8. `008_create_salary_grids.sql`
9. `009_create_salary_grid_lines.sql`
10. `010_create_seasons.sql`
11. `011_create_periods.sql`
12. `012_create_activities_places_timeslots.sql`
13. `013_create_time_natures.sql`
14. `014_create_assignments.sql`
15. `015_create_calculation_rules.sql`
16. `016_create_calculation_results.sql`
17. `017_create_anomalies.sql`
18. `018_create_individual_counters.sql`

## Remarque
Les types SQL sont volontairement simples pour rester lisibles. Ils devront être adaptés ensuite au moteur réel de persistance du dépôt Teamworks.
