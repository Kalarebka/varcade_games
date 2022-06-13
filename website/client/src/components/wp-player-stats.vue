<template>

    <div>
            
        <h2>
            Your Stats
        </h2>

        <hr/>
        
        <div class="info-box-bg ps-container" v-bind:class="{ 'info-box-empty': !statsLoaded || !statsRecorded }">
            <div v-if="playerGameStats">
                <div v-if="statsRecorded">
                    <div class="row ps-row" v-for="(value) in playerGameStats" :key="`${ value }`">
                        <div class="col">{{ value[0] }}</div>
                        <div class="col">{{ value[1] }}</div>
                    </div>
                </div>
                <div v-else class="info-box-layout">
                    <div>
                        <h5>Looks like you haven't played this game online yet, what are you waiting for?</h5>
                        <p>As you play your stats will be updated here.</p>
                    </div>
                </div>
            </div>
            <div v-else>
                <div>
                    <p>Loading stats...</p>
                    <font-awesome-icon class="red-ico" :icon="loadingSpinner" spin size="4x"/>
                </div>
            </div>
        </div> 
                
    </div>

</template>

<script>

    import axios from 'axios';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
    import { faSpinner } from '@fortawesome/free-solid-svg-icons'

    import {runWithRetries} from '../utils.js';

    export default {
        name: 'player-stats',
        props: {
            'selectedGame': Object
        },
        components: {FontAwesomeIcon},
        data () {
            return {
                playerGameStats: null,
                translationData: null,
                loadingSpinner: faSpinner
            }
        },
        computed: {
            statsLoaded: function () {
                return this.playerGameStats != null
            },
            statsRecorded: function () {
                return this.playerGameStats != null && this.playerGameStats.length > 0
            }
        },
        methods: {

            loadPlayerGameStats: function (onError) {
                const statsUrl = `${this.$store.state.serverUrl}/games/${this.$store.state.apiVersion}/stats/${this.selectedGame.game_id}/`;

                const customStatsUrl = this.selectedGame.stats_config
                axios.get(customStatsUrl).then(resp => {
                    const statsFormat = resp.data;
                    
                    axios.get(statsUrl).then(resp => {
                        this.processCustomStats(statsFormat, resp.data)
                    }).catch((error) => {
                      onError(error)
                    });

                }).catch((error) => {
                  console.error('Unable to download game specific stats format file.')
                  onError(error)
                });
            },
            processCustomStats: function (statsFormat, statsData) {
                this.playerGameStats = []
                if (statsFormat && statsData) {
                    statsFormat.stat_ordering.forEach(entry => {
                        if (statsData[entry]) {
                            this.playerGameStats.push([`
                                ${statsFormat.strings.en[entry]}`,
                                `${statsData[entry]}`]
                            )
                        }
                    })
                }
                else {
                    console.error("Unable to process custom stats - format or stats data missing.")
                }
            }
        },

        mounted: function () {
            runWithRetries(this.loadPlayerGameStats, []);
        }
    }

</script>

<style>

    .ps-row {
    font-weight: bold;
    border-bottom: 1px solid #ff48484a;
    padding-top: 1em;
    padding-bottom: 1em;
    }

    .ps-container {
        overflow-x: hidden;
        overflow-y: auto;
    }


</style>
