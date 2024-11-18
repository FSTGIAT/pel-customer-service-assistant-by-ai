<template>
  <div :class="['flex', message.type === 'user' ? 'justify-end' : 'justify-start']">
    <div :class="['flex items-start space-x-2 max-w-[80%]']">
      <div v-if="message.type === 'bot'" 
           class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
        <i class="fas fa-robot text-blue-600"></i>
      </div>
      <div :class="bubbleClasses">
        {{ message.content }}
      </div>
      <div v-if="message.type === 'user'" 
           class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
        <i class="fas fa-user text-gray-600"></i>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
});

const bubbleClasses = computed(() => {
  return [
    'p-3 rounded-lg',
    {
      'bg-blue-600 text-white': props.message.type === 'user',
      'bg-gray-100 text-gray-800': props.message.type === 'bot',
      'bg-gray-100 text-gray-500 text-sm w-full text-center': props.message.type === 'system'
    }
  ];
});
</script>
