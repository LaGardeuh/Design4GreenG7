<script lang="ts">
    let text = $state("");
    const maxChars = 4000;
    let optimize = $state(false);

    let consumption = $state(0);
    let latency = $state(0);
    let summary = $state("");
    let isLoading = $state(false);

    // Pour la comparaison :
    let optimizedSummary = $state("");
    let nonOptimizedSummary = $state("");
    let latencyGain = $state(0);
    let energyGain = $state(0);
    let latencyOpt = $state(0);
    let latencyNonOpt = $state(0);
    let wordCountOpt = $state(0);
    let wordCountNonOpt = $state(0);

    function handleInput(e: Event) {
        const target = e.target as HTMLTextAreaElement;
        text = target.value;
    }

    async function handleSummarize() {
        if (!text || isLoading) return;
        isLoading = true;
        try {
            const response = await fetch("/summarize", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ textToSum: text, optimized: optimize })
            });
            const data = await response.json();
            if (data.success) {
                summary = data.results.summary;
                latency = data.results.latency;
                consumption = data.results.energy_wh
                    ? Number(data.results.energy_wh.toFixed(6))
                    : 0;

                // reset comparaison
                optimizedSummary = "";
                nonOptimizedSummary = "";
                latencyGain = 0;
                energyGain = 0;
                latencyOpt = 0;
                latencyNonOpt = 0;
                wordCountOpt = 0;
                wordCountNonOpt = 0;
            } else alert(`Erreur: ${data.error}`);
        } catch (err) {
            console.error(err);
            alert("Erreur serveur, impossible de générer le résumé");
        } finally {
            isLoading = false;
        }
    }

    async function handleCompare() {
        if (!text || isLoading) return;
        isLoading = true;
        try {
            const response = await fetch("/compare", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ textToSum: text })
            });
            const data = await response.json();

            if (data.success) {
                optimizedSummary = data.comparison.optimized.summary;
                nonOptimizedSummary = data.comparison.non_optimized.summary;
                latencyGain = data.comparison.performance_gains.latency_reduction_percent;
                energyGain = data.comparison.performance_gains.energy_reduction_percent;
                latencyOpt = data.comparison.performance_gains.latency_optimized_ms;
                latencyNonOpt = data.comparison.performance_gains.latency_non_optimized_ms;

                // 🆕 Récupère les nombres de mots
                wordCountOpt = data.comparison.optimized.word_count;
                wordCountNonOpt = data.comparison.non_optimized.word_count;

                summary = "";
            } else alert(`Erreur: ${data.error}`);
        } catch (err) {
            console.error(err);
            alert("Erreur serveur, impossible de comparer les modèles");
        } finally {
            isLoading = false;
        }
    }

    function handleClean() {
        text = "";
        summary = "";
        latency = 0;
        consumption = 0;
        optimizedSummary = "";
        nonOptimizedSummary = "";
        latencyGain = 0;
        energyGain = 0;
        latencyOpt = 0;
        latencyNonOpt = 0;
        wordCountOpt = 0;
        wordCountNonOpt = 0;
    }
</script>

<!-- === interface === -->
{#if optimizedSummary || nonOptimizedSummary}
    <div class="grid md:grid-cols-2 gap-4">
        <div class="bg-card border border-border rounded-lg p-4">
            <div class="text-sm text-muted-foreground mb-1">Optimised:</div>
            <p class="text-foreground text-lg whitespace-pre-wrap">{optimizedSummary}</p>
        </div>

        <div class="bg-card border border-border rounded-lg p-4">
            <div class="text-sm text-muted-foreground mb-1">Non Optimized:</div>
            <p class="text-foreground text-lg whitespace-pre-wrap">{nonOptimizedSummary}</p>
        </div>
    </div>

    <div class="grid grid-cols-2 gap-4 mt-4">
        <div class="bg-card border border-border rounded-lg p-4 text-center">
            <div class="text-sm text-muted-foreground mb-1">Latency gain</div>
            <div class="text-2xl font-bold text-green-500">-{latencyGain}%</div>
        </div>

        <div class="bg-card border border-border rounded-lg p-4 text-center">
            <div class="text-sm text-muted-foreground mb-1">Energy gain</div>
            <div class="text-2xl font-bold text-green-500">-{energyGain}%</div>
        </div>
    </div>

    <!-- Ajout latences + nombre de mots -->
    <div class="grid grid-cols-2 gap-4 mt-4">
        <div class="bg-card border border-border rounded-lg p-4 text-center">
            <div class="text-sm text-muted-foreground mb-1">Latency (non optimized)</div>
            <div class="text-xl font-semibold text-foreground">{latencyNonOpt} ms</div>
            <div class="text-sm text-muted-foreground mt-1">Word count: {wordCountNonOpt}</div>
        </div>

        <div class="bg-card border border-border rounded-lg p-4 text-center">
            <div class="text-sm text-muted-foreground mb-1">Latency (optimized)</div>
            <div class="text-xl font-semibold text-foreground">{latencyOpt} ms</div>
            <div class="text-sm text-muted-foreground mt-1">Word count: {wordCountOpt}</div>
        </div>
    </div>
{/if}
