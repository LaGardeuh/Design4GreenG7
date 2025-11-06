<script lang="ts">
    let text = $state("");
    const maxChars = 4000;
    let optimize = $state(false);
    let language = $state("fr");

    // ✅ Initialise à 0
    let consumption = $state(0);
    let latency = $state(0);
    let summary = $state("");

    function handleInput(e: Event) {
        const target = e.target as HTMLTextAreaElement;
        text = target.value;
    }

    async function handleSummarize() {
        if (!text) return;

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
                // ✅ met à jour consommation avec valeur réelle ou 0
                consumption = data.results.energy_wh
                    ? Number(data.results.energy_wh.toFixed(6))
                    : 0;
            } else {
                alert(`Erreur: ${data.error}`);
            }
        } catch (err) {
            console.error(err);
            alert("Erreur serveur, impossible de générer le résumé");
        }
    }

    async function handleCompare() {
        if (!text) return;

        try {
            const response = await fetch("/compare", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ textToSum: text })
            });

            const data = await response.json();

            if (data.success) {
                alert(
                    `Comparaison Optimisé vs Non-optimisé :\n\n` +
                    `Optimisé:\n${data.comparison.optimized.summary}\n\n` +
                    `Non-optimisé:\n${data.comparison.non_optimized.summary}\n\n` +
                    `Gains : Latence ${data.comparison.performance_gains.latency_reduction_percent}% / Énergie ${data.comparison.performance_gains.energy_reduction_percent}%`
                );
            } else {
                alert(`Erreur: ${data.error}`);
            }
        } catch (err) {
            console.error(err);
            alert("Erreur serveur, impossible de comparer les modèles");
        }
    }

    function handleClean() {
        text = "";
        summary = "";
        latency = 0;
        consumption = 0; // ✅ force reset propre
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
                value={text}
                oninput={handleInput}
                maxlength={maxChars}
        ></textarea>

                <div
                        class="absolute bottom-4 right-4 text-sm font-mono text-muted-foreground"
                >
                    {text.length}/{maxChars}
                </div>
            </div>

            <div
                    class="flex flex-wrap gap-4 items-center justify-between pt-4 border-t border-border"
            >
                <div class="flex flex-wrap gap-4 items-center">
                    <select
                            bind:value={language}
                            class="border border-border rounded-lg px-4 py-2 text-foreground outline-none focus:ring-2 focus:ring-primary/50"
                            style="background-color: rgb(var(--color-card));"
                    >
                        <option value="fr">🇫🇷 French</option>
                        <option value="en">🇬🇧 English</option>
                    </select>

                    <label class="flex items-center gap-2 cursor-pointer">
                        <input
                                type="checkbox"
                                bind:checked={optimize}
                                class="w-4 h-4 rounded border-border text-primary focus:ring-2 focus:ring-primary/50"
                        />
                        <span class="text-sm text-muted-foreground">Optimiser</span>
                    </label>
                </div>

                <div class="flex gap-3">
                    <button
                            onclick={handleClean}
                            class="px-5 py-2 rounded-lg font-medium bg-secondary text-foreground border border-border hover:bg-secondary/80"
                    >
                        Clean
                    </button>
                    <button
                            onclick={handleSummarize}
                            disabled={text.length === 0}
                            class="px-6 py-2 rounded-lg font-medium bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                    >
                        Summarize
                    </button>
                    <button
                            onclick={handleCompare}
                            disabled={text.length === 0}
                            class="px-6 py-2 rounded-lg font-medium bg-accent text-accent-foreground hover:bg-accent/90 disabled:opacity-50"
                    >
                        Compare Models
                    </button>
                </div>
            </div>
        </div>

        {#if summary}
            <div class="bg-card border border-border rounded-lg p-4">
                <div class="text-sm text-muted-foreground mb-1">Résumé généré :</div>
                <p class="text-foreground text-lg">{summary}</p>
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
