<script lang="ts">
    let text = $state("");
    const maxChars = 4000;
    let optimize = $state(false);
    let language = $state("fr");
    let consumption = $state(0.42);
    let latency = $state(0);

    function handleInput(e: Event) {
        const target = e.target as HTMLTextAreaElement;
        text = target.value;
    }

    function handleSummarize() {
        const start = performance.now();
        setTimeout(() => {
            latency = Math.round(performance.now() - start);
            consumption = Number((consumption + 0.05).toFixed(2));
            alert(`Résumé (${language}):\n${text.slice(0, 200)}...`);
        }, Math.random() * 500 + 200);
    }
</script>

<main class="min-h-screen flex items-center justify-center p-4 bg-background">
    <div class="w-full max-w-4xl space-y-6">
        <!-- Header -->
        <div class="text-center space-y-2">
            <h1 class="text-4xl font-bold text-foreground">D4G Summarizer by Thomas,Malo,Aubin</h1>
            <p class="text-muted-foreground">Summarize your text under 4000 caracters</p>
        </div>

        <!-- Main Card -->
        <div class="bg-card border border-border rounded-xl p-6 space-y-4">
            <!-- Textarea -->
            <div class="relative">
				<textarea
                        class="w-full h-64 p-4 border border-border rounded-lg resize-none
					       focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none
					       text-foreground placeholder:text-muted-foreground color-background"
                        style="background-color: rgb(var(--color-textarea));"
                        placeholder="Paste your text here..."
                        value={text}
                        oninput={handleInput}
                        maxlength={maxChars}
                ></textarea>

                <div class="absolute bottom-4 right-4 text-sm font-mono text-muted-foreground">
                    {text.length}/{maxChars}
                </div>
            </div>

            <!-- Controls -->
            <div class="flex flex-wrap gap-4 items-center justify-between pt-4 border-t border-border">
                <div class="flex flex-wrap gap-4 items-center">

                    <select
                            bind:value={language}
                            class="border border-border rounded-lg px-4 py-2 text-foreground outline-none focus:ring-2 focus:ring-primary/50">
                        style="background-color: rgb(var(--color-card));"
                        >
                        <option value="fr">🇫🇷 French</option>
                        <option value="en">🇬🇧 English</option>
                        <!--<option value="es">🇪🇸 Español</option>-->
                    </select>

                    <!-- Optimize -->
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" bind:checked={optimize} class="w-4 h-4 rounded border-border text-primary focus:ring-2 focus:ring-primary/50" />
                        <span class="text-sm text-muted-foreground">Optimiser</span>
                    </label>
                </div>

                <!-- Buttons Effacer/Summarize/Comparer les 2 modeles -->
                <div class="flex gap-3">
                    <button
                            onclick={() => text = ""}
                            class="px-5 py-2 rounded-lg font-medium bg-secondary text-foreground border border-border hover:bg-secondary/80"
                    >
                        Clean
                    </button>
                    <button
                            onclick={handleSummarize}
                            disabled={text.length === 0}
                            class="px-6 py-2 rounded-lg font-medium bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                    >
                        Sumarize
                    </button>
                </div>
            </div>
        </div>

        <!-- Dashboard -->
        <div class="grid grid-cols-2 gap-4">
            <div class="bg-card border border-border rounded-lg p-4">
                <div class="text-sm text-muted-foreground mb-1">Consommation</div>
                <div class="text-2xl font-bold text-foreground">{consumption} kWh</div>
            </div>

            <div class="bg-card border border-border rounded-lg p-4">
                <div class="text-sm text-muted-foreground mb-1">Latence</div>
                <div class="text-2xl font-bold text-foreground">{latency} ms</div>
            </div>
        </div>
    </div>
</main>
