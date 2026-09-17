<script setup>
import { ref } from 'vue';
const count = ref(0);
</script>
<template>
  <div class="demo"><p>Vue 3 component · client-side interaction</p><button @click="count++">Say hello</button><span role="status"> {{ count }} hello{{ count === 1 ? '' : 's' }}</span></div>
</template>
