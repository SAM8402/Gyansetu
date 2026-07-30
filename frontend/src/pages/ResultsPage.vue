<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-semibold">{{ tkp?.metadata?.topic || 'Results' }}</h1>
      <a v-if="tkp" :href="`/api/jobs/${$route.params.id}/tkp`" class="text-sm px-4 py-1.5 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 inline-block" download>Download JSON</a>
    </div>

    <div v-if="loading" class="border border-gray-200 rounded-lg p-6"><LoadingSkeleton height="240px" /></div>
    <div v-else-if="!tkp" class="border border-gray-200 rounded-lg p-12 text-center text-gray-400"><p>No results yet.</p></div>

    <template v-else>
      <div class="flex gap-1 mb-4 flex-wrap">
        <button v-for="tab in tabs" :key="tab.key" :class="['text-sm px-3.5 py-1.5 rounded-lg transition', tabCls(tab.key)]" @click="activeTab = tab.key">{{ tab.label }}</button>
      </div>

      <div class="border border-gray-200 rounded-lg p-6 min-h-[160px]">
        <div v-if="activeTab === 'overview'">
          <div class="grid grid-cols-3 gap-4 mb-6">
            <div><strong class="text-xs text-gray-400">Subject</strong><p class="text-sm mt-0.5">{{ tkp.metadata.subject }}</p></div>
            <div><strong class="text-xs text-gray-400">Grade</strong><p class="text-sm mt-0.5">{{ tkp.metadata.grade }}</p></div>
            <div><strong class="text-xs text-gray-400">Difficulty</strong><p class="text-sm mt-0.5">{{ tkp.metadata.difficulty }}</p></div>
            <div><strong class="text-xs text-gray-400">Language</strong><p class="text-sm mt-0.5">{{ tkp.metadata.language }}</p></div>
            <div><strong class="text-xs text-gray-400">Board</strong><p class="text-sm mt-0.5">{{ tkp.metadata.board_alignment }}</p></div>
            <div><strong class="text-xs text-gray-400">Periods</strong><p class="text-sm mt-0.5">{{ tkp.metadata.total_periods }}</p></div>
          </div>
          <h3 class="text-sm font-semibold mb-2">Learning Objectives</h3>
          <ul class="text-sm pl-5 space-y-1"><li v-for="o in tkp.knowledge_base?.learning_objectives" :key="o">{{ o }}</li></ul>
        </div>

        <div v-if="activeTab === 'plans'">
          <div v-for="p in tkp.teaching_plan?.periods" :key="p.period_number" class="mb-4 p-4 bg-gray-50 rounded-lg">
            <h3 class="text-sm font-semibold mb-2">Period {{ p.period_number }}: {{ p.title }} ({{ p.duration_minutes }} min)</h3>
            <p v-if="p.entry_ticket" class="text-sm text-gray-600"><strong>Entry:</strong> {{ p.entry_ticket.question }}</p>
            <p v-if="p.exit_ticket" class="text-sm text-gray-600 mt-1"><strong>Exit:</strong> {{ p.exit_ticket.question }}</p>
          </div>
        </div>

        <div v-if="activeTab === 'assessments'">
          <div v-for="(q, i) in tkp.assessments?.mcqs" :key="i" class="mb-3 p-3 bg-gray-50 rounded-lg">
            <p class="text-sm"><strong>{{ i + 1 }}.</strong> {{ q.question }} <span :class="['text-xs px-1.5 py-0.5 rounded', diffCls(q.difficulty)]">{{ q.difficulty }}</span></p>
            <p class="text-xs text-gray-400 mt-2">Answer: {{ q.correct_answer }}</p>
          </div>
        </div>

        <div v-if="activeTab === 'activities'">
          <div v-for="(acts, pi) in tkp.teaching_plan?.periods" :key="pi" class="mb-4 p-4 bg-gray-50 rounded-lg">
            <h3 class="text-sm font-semibold mb-2">Period {{ acts.period_number }}</h3>
            <div v-for="(a, i) in acts.classroom_activities" :key="i" class="mb-2 p-3 bg-white rounded-lg text-sm">
              <p><strong>{{ a.title }}</strong> — {{ a.type }}, {{ a.duration_minutes }} min</p>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'gaps'">
          <div v-for="g in tkp.learning_gaps" :key="g.gap_id" class="mb-3 p-3 bg-gray-50 rounded-lg">
            <p class="text-sm"><strong>{{ g.description }}</strong></p>
            <p class="text-xs text-gray-400 mt-2">Severity: {{ g.severity }} — Remedial: {{ g.remedial_action }}</p>
          </div>
        </div>

        <div v-if="activeTab === 'validation'">
          <p class="text-sm"><strong>Schema valid:</strong> {{ tkp.validation_report?.schema_valid ? 'Yes' : 'No' }}</p>
          <p class="text-sm mt-2"><strong>Completeness:</strong> {{ (tkp.validation_report?.completeness_score * 100).toFixed(0) }}%</p>
          <p v-if="tkp.validation_report?.missing_elements?.length" class="text-sm mt-2"><strong>Missing:</strong> {{ tkp.validation_report.missing_elements.join(', ') }}</p>
        </div>
      </div>
    </template>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useJobsStore } from '../stores/jobs'
import LoadingSkeleton from '../components/common/LoadingSkeleton.vue'
const route = useRoute()
const { fetchJob } = useJobsStore()
const tkp = ref(null), loading = ref(true), activeTab = ref('overview')
const tabs = [
  { key: 'overview', label: 'Overview' }, { key: 'plans', label: 'Lesson Plans' },
  { key: 'assessments', label: 'Assessments' }, { key: 'activities', label: 'Activities' },
  { key: 'gaps', label: 'Gaps' }, { key: 'validation', label: 'Validation' },
]
function tabCls(key) { return activeTab.value === key ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200' }
function diffCls(d) { return { easy: 'bg-green-100 text-green-700', medium: 'bg-yellow-100 text-yellow-700', hard: 'bg-red-100 text-red-700' }[d] || '' }
onMounted(async () => {
  try {
    const job = await fetchJob(route.params.id)
    if (job.status === 'completed') {
      const { data } = await import('../api/jobs').then(m => m.downloadTkp(route.params.id))
      tkp.value = data
    }
  } finally { loading.value = false }
})
</script>
