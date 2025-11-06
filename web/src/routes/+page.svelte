<script lang="ts">
    // états "runes" Svelte 5
    let text = $state("");
    const maxChars = 4000;
    let optimize = $state(false);

    // stats simples
    let consumption = $state(0);
    let latency = $state(0);
    let summary = $state("");
    let isLoading = $state(false);

    // comparaison
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
                body: JSON.stringify({
                    textToSum: text,
                    optimized: optimize
                })
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
            } else {
                alert(`Erreur: ${data.error}`);
            }
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
                // résumés
                optimizedSummary = data.comparison.optimized.summary;
                nonOptimizedSummary = data.comparison.non_optimized.summary;

                // gains
                latencyGain = data.comparison.performance_gains.latency_reduction_percent;
                energyGain = data.comparison.performance_gains.energy_reduction_percent;

                // latences
                latencyOpt =
                    data.comparison.performance_gains.latency_optimized_ms ??
                    data.comparison.optimized.latency ??
                    0;

                latencyNonOpt =
                    data.comparison.performance_gains.latency_non_optimized_ms ??
                    data.comparison.non_optimized.latency ??
                    0;

                // word counts
                wordCountOpt = data.comparison.optimized.word_count ?? 0;
                wordCountNonOpt = data.comparison.non_optimized.word_count ?? 0;

                summary = "";
            } else {
                alert(`Erreur: ${data.error}`);
            }
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

<main class="min-h-screen flex items-center justify-center p-4 bg-background">
    <div class="w-full max-w-4xl space-y-6">
        <div class="text-center space-y-2">
            <h1 class="text-4xl font-bold text-foreground">
                D4G Summarizer by Thomas, Malo, Aubin
            </h1>
            <p class="text-muted-foreground">Summarize your text under 4000 characters</p>
        </div>

        <!-- bloc input -->
        <div class="bg-card border border-border rounded-xl p-6 space-y-4">
            <div class="relative">
                <textarea
                        class="w-full h-64 p-4 border border-border rounded-lg resize-none
                    focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none
                    text-foreground placeholder:text-muted-foreground"
                        style="background-color: rgb(var(--color-card));"
                        placeholder="Paste your text here..."
                        bind:value={text}
                        on:input={handleInput}
                        maxlength={maxChars}
                        disabled={isLoading}
                ></textarea>

                <div class="absolute bottom-4 right-4 text-sm font-mono text-muted-foreground">
                    {text.length}/{maxChars}
                </div>
            </div>

            <div class="flex flex-wrap gap-4 items-center justify-between pt-4 border-t border-border">
                <div class="flex flex-wrap gap-4 items-center">
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" bind:checked={optimize} class="hidden peer" disabled={isLoading} />
                        <span
                                class="w-5 h-5 rounded-full border border-gray-500 flex items-center justify-center
                            peer-checked:bg-green-500 peer-checked:border-green-500 transition-all duration-200"
                        >
                            <svg
                                    class="w-3 h-3 text-white opacity-0 peer-checked:opacity-100 transition-opacity"
                                    xmlns="http://www.w3.org/2000/svg"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                    stroke-width="3"
                            >
                                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                        </span>
                        <span class="text-sm text-muted-foreground">Optimiser</span>
                    </label>
                </div>

                <div class="flex gap-3">
                    <button
                            on:click={handleClean}
                            class="px-5 py-2 rounded-lg font-medium bg-green-700 text-white hover:bg-green-800 transition-colors"
                            disabled={isLoading}
                    >
                        Clean
                    </button>

                    <button
                            on:click={handleSummarize}
                            disabled={text.length === 0 || isLoading}
                            class="px-6 py-2 rounded-lg font-medium bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition-colors"
                    >
                        {isLoading ? "Loading..." : "Summarize"}
                    </button>

                    <button
                            on:click={handleCompare}
                            disabled={text.length === 0 || isLoading}
                            class="px-6 py-2 rounded-lg font-medium bg-green-500 text-white hover:bg-green-600 disabled:opacity-50 transition-colors"
                    >
                        {isLoading ? "Loading..." : "Compare Models"}
                    </button>
                </div>
            </div>
        </div>

        <!-- résumé simple -->
        {#if summary}
            <div class="bg-card border border-border rounded-lg p-4">
                <div class="text-sm text-muted-foreground mb-1">Generated summary:</div>
                <p class="text-foreground text-lg whitespace-pre-wrap">{summary}</p>
            </div>
        {/if}

        <!-- === COMPARAISON === -->
        {#if optimizedSummary || nonOptimizedSummary}
            <div class="bg-card border border-border rounded-xl p-6 space-y-6 mt-6">
                <h2 class="text-2xl font-semibold text-center text-foreground">Model Comparison</h2>

                <!-- Résumés -->
                <div class="grid md:grid-cols-2 gap-4">
                    <div class="bg-muted/20 border border-border rounded-lg p-4">
                        <div class="text-sm text-muted-foreground mb-1 font-medium">Non Optimized</div>
                        <p class="text-foreground text-base whitespace-pre-wrap leading-relaxed">
                            {nonOptimizedSummary}
                        </p>
                    </div>

                    <div class="bg-muted/20 border border-border rounded-lg p-4">
                        <div class="text-sm text-muted-foreground mb-1 font-medium">Optimized</div>
                        <p class="text-foreground text-base whitespace-pre-wrap leading-relaxed">
                            {optimizedSummary}
                        </p>
                    </div>
                </div>

                <!-- Tableau comparatif -->
                <div class="overflow-x-auto">
                    <table class="w-full border border-border rounded-lg text-sm text-foreground">
                        <thead class="bg-muted text-muted-foreground uppercase tracking-wide">
                        <tr>
                            <th class="border border-border p-2 text-left">Metric</th>
                            <th class="border border-border p-2 text-center">Non Optimized</th>
                            <th class="border border-border p-2 text-center">Optimized</th>
                            <th class="border border-border p-2 text-center text-green-500">Gain</th>
                        </tr>
                        </thead>
                        <tbody>
                        <tr>
                            <td class="border border-border p-2">Latency (ms)</td>
                            <td class="border border-border p-2 text-center">{latencyNonOpt}</td>
                            <td class="border border-border p-2 text-center">{latencyOpt}</td>
                            <td class="border border-border p-2 text-center text-green-500">
                                -{latencyGain}%
                            </td>
                        </tr>
                        <tr>
                            <td class="border border-border p-2">Energy (Wh)</td>
                            <td class="border border-border p-2 text-center">—</td>
                            <td class="border border-border p-2 text-center">—</td>
                            <td class="border border-border p-2 text-center text-green-500">
                                -{energyGain}%
                            </td>
                        </tr>
                        <tr>
                            <td class="border border-border p-2">Word count</td>
                            <td class="border border-border p-2 text-center">{wordCountNonOpt}</td>
                            <td class="border border-border p-2 text-center">{wordCountOpt}</td>
                            <td class="border border-border p-2 text-center text-green-500">
                                {wordCountNonOpt && wordCountOpt
                                    ? Math.round(
                                        ((wordCountNonOpt - wordCountOpt) / wordCountNonOpt) * 100
                                    )
                                    : 0}%
                            </td>
                        </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        {/if}

        <!-- stats globales -->
        <div class="grid grid-cols-2 gap-4">
            <div class="bg-card border border-border rounded-lg p-4">
                <div class="text-sm text-muted-foreground mb-1">Consumption</div>
                <div class="text-2xl font-bold text-foreground">{consumption} Wh</div>
            </div>

            <div class="bg-card border border-border rounded-lg p-4">
                <div class="text-sm text-muted-foreground mb-1">Latency</div>
                <div class="text-2xl font-bold text-foreground">{latency} ms</div>
            </div>
        </div>
    </div>
</main>
