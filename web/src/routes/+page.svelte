<script lang="ts">
    let text = $state("");
    const maxChars = 4000;
    let optimize = $state(false);

    let consumption = $state(0);
    let latency = $state(0);
    let summary = $state("");
    let isLoading = $state(false);

    // Pour le mode comparaison :
    let optimizedSummary = $state("");
    let nonOptimizedSummary = $state("");
    let latencyGain = $state(0);
    let energyGain = $state(0);

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

                // Réinitialise la comparaison s’il y en avait une
                optimizedSummary = "";
                nonOptimizedSummary = "";
                latencyGain = 0;
                energyGain = 0;
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
                optimizedSummary = data.comparison.optimized.summary;
                nonOptimizedSummary = data.comparison.non_optimized.summary;
                latencyGain = data.comparison.performance_gains.latency_reduction_percent;
                energyGain = data.comparison.performance_gains.energy_reduction_percent;

                // Efface l’ancien résumé
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
    }
</script>

<main class="min-h-screen flex items-center justify-center p-4 bg-background">
    <div class="w-full max-w-4xl space-y-6">
        <div class="text-center space-y-2">
            <h1 class="text-4xl font-bold text-foreground">
                D4G Summarizer by Thomas, Malo, Aubin
            </h1>
            <p class="text-muted-foreground">
                Summarize your text under 4000 characters
            </p>
        </div>

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
                        <input
                                type="checkbox"
                                bind:checked={optimize}
                                class="hidden peer"
                                disabled={isLoading}
                        />
                        <span class="w-5 h-5 rounded-full border border-gray-500 flex items-center justify-center
                            peer-checked:bg-green-500 peer-checked:border-green-500 transition-all duration-200">
                            <svg
                                    class="w-3 h-3 text-white opacity-0 peer-checked:opacity-100 transition-opacity"
                                    xmlns="http://www.w3.org/2000/svg"
                                    fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
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

        {#if summary}
            <div class="bg-card border border-border rounded-lg p-4">
                <div class="text-sm text-muted-foreground mb-1">Résumé généré :</div>
                <p class="text-foreground text-lg whitespace-pre-wrap">{summary}</p>
            </div>
        {/if}

        {#if optimizedSummary || nonOptimizedSummary}
            <div class="grid md:grid-cols-2 gap-4">
                <div class="bg-card border border-border rounded-lg p-4">
                    <div class="text-sm text-muted-foreground mb-1">Optimisé :</div>
                    <p class="text-foreground text-lg whitespace-pre-wrap">{optimizedSummary}</p>
                </div>

                <div class="bg-card border border-border rounded-lg p-4">
                    <div class="text-sm text-muted-foreground mb-1">Non optimisé :</div>
                    <p class="text-foreground text-lg whitespace-pre-wrap">{nonOptimizedSummary}</p>
                </div>
            </div>

            <div class="grid grid-cols-2 gap-4 mt-4">
                <div class="bg-card border border-border rounded-lg p-4 text-center">
                    <div class="text-sm text-muted-foreground mb-1">Gain en latence</div>
                    <div class="text-2xl font-bold text-green-500">-{latencyGain}%</div>
                </div>

                <div class="bg-card border border-border rounded-lg p-4 text-center">
                    <div class="text-sm text-muted-foreground mb-1">Gain en énergie</div>
                    <div class="text-2xl font-bold text-green-500">-{energyGain}%</div>
                </div>
            </div>
        {/if}

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
