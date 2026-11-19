-- One record per assigned customer. Non-visitors stay in all denominators.
SELECT
    segment AS arm,
    COUNT(*) AS assigned,
    SUM(visit) AS visitors,
    SUM(conversion) AS buyers,
    AVG(1.0 * conversion) AS purchase_rate,
    SUM(spend_cents) AS total_spend_cents,
    SUM(spend_cents) / (100.0 * COUNT(*)) AS spend_per_assigned
FROM assignments
GROUP BY segment
ORDER BY CASE segment
    WHEN 'No E-Mail' THEN 1
    WHEN 'Mens E-Mail' THEN 2
    WHEN 'Womens E-Mail' THEN 3
END;
