<template>

    <div>    
        <h2>
            Leaderboard
        </h2>
        <hr/>
        <div class="info-box-bg lb-container"  
             v-bind:class="{ 'info-box-empty': !leaderboardLoaded || !leaderboardScoresRecorded }">
            <div v-if="leaderboard">
                <div v-if="leaderboard.length > 0">
                    
                    <div class="row lb-row lb-header">
                        <div class="col">Username</div>    
                        <div class="col">Wins</div>
                    </div>

                    <div class="row lb-row" v-for="(entry, index) in leaderboard" :key="entry.user_id">
                        <div class="col">{{ index + 1 }}. {{ entry.username}}</div>    
                        <div class="col">{{entry.score}}</div>
                    </div>
                
                </div>
                <div v-else class="info-box-layout">
                    <div>
                        <h5>No one has registered a score on the leaderboard yet!</h5>
                        <p>Play now to get your name on top!</p>
                    </div>
                </div>
            </div>
            <div v-else>
                <p>Loading Leaderboard...</p>
                <font-awesome-icon class="red-ico" :icon="loadingSpinner" spin size="4x"/>
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
        name: 'game-leaderboard',
        props: ['gameId'],
        components: {FontAwesomeIcon},
        data () {
            return {
                leaderboard: null,
                loadingSpinner: faSpinner
            }
        },
        computed: {
            leaderboardLoaded: function () {
                return this.leaderboard != null
            },
            leaderboardScoresRecorded: function () {
                return this.leaderboard != null && this.leaderboard.length > 0
            }
        },
        methods: {

            loadLeaderboard: function (onError) {
                const leaderboardUrl = 
                    `${this.$store.state.serverUrl}/games/${this.$store.state.apiVersion}/leaderboard/${this.gameId}/`

                axios.get(leaderboardUrl).then(resp => {
                    this.leaderboard = resp.data;
                }).catch((error) => {
                  onError(error)
                });
            }

        },
        
        mounted: function () {
            runWithRetries(this.loadLeaderboard, []);
        }
    }

</script>

<style>

    .lb-row {
        font-weight: bold;
        border-bottom: 1px solid #ff48484a;
        padding-top: 1em;
        padding-bottom: 1em;
    }

    .lb-header {
        color: #ff4848;
        font-size: 18px;
    }

    .lb-container {
        overflow-x: hidden;
        overflow-y: auto;
    }

</style>
