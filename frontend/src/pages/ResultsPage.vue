<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">{{ tkp?.metadata?.topic || 'Teacher Knowledge Package' }}</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1" v-if="tkp?.metadata">
          {{ tkp.metadata.subject }} • {{ tkp.metadata.grade }} • {{ tkp.metadata.total_periods }} Periods ({{ tkp.metadata.period_duration_minutes }} min each)
        </p>
      </div>
      <div class="flex items-center gap-3">
        <a v-if="tkp" :href="`/api/jobs/${$route.params.id}/tkp`" class="text-sm px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium shadow-sm transition inline-flex items-center gap-1.5" download>
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
          Download TKP JSON
        </a>
        <button @click="handleDelete" class="text-sm px-4 py-2 rounded-lg border border-red-200 dark:border-red-900/60 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 font-medium transition">Delete</button>
      </div>
    </div>

    <div v-if="loading" class="border border-gray-200 dark:border-gray-800 rounded-xl p-8 bg-white dark:bg-gray-900 shadow-sm"><LoadingSkeleton height="280px" /></div>
    <div v-else-if="!tkp" class="border border-gray-200 dark:border-gray-800 rounded-xl p-12 text-center text-gray-400 dark:text-gray-500 bg-white dark:bg-gray-900"><p>No results available for this document.</p></div>
    <template v-else>
      <div class="flex gap-2 mb-6 border-b border-gray-200 dark:border-gray-800 pb-3 flex-wrap">
        <button v-for="tab in tabs" :key="tab.key" :class="['text-sm px-4 py-2 rounded-lg transition font-medium', tabCls(tab.key)]" @click="activeTab = tab.key">
          {{ tab.label }}
        </button>
      </div>

      <div class="border border-gray-200 dark:border-gray-800 rounded-xl p-6 bg-white dark:bg-gray-900 shadow-sm text-gray-900 dark:text-gray-100">
        <!-- Overview Tab -->
        <div v-if="activeTab === 'overview'">
          <h2 class="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Metadata & Classification</h2>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div class="p-3 bg-gray-50 dark:bg-gray-800/60 rounded-lg"><strong class="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wider block mb-0.5">Subject</strong><p class="text-sm font-semibold">{{ tkp.metadata.subject }}</p></div>
            <div class="p-3 bg-gray-50 dark:bg-gray-800/60 rounded-lg"><strong class="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wider block mb-0.5">Grade</strong><p class="text-sm font-semibold">{{ tkp.metadata.grade }}</p></div>
            <div class="p-3 bg-gray-50 dark:bg-gray-800/60 rounded-lg"><strong class="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wider block mb-0.5">Difficulty</strong><p class="text-sm font-semibold capitalize">{{ tkp.metadata.difficulty }}</p></div>
            <div class="p-3 bg-gray-50 dark:bg-gray-800/60 rounded-lg"><strong class="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wider block mb-0.5">Board Alignment</strong><p class="text-sm font-semibold">{{ tkp.metadata.board_alignment }}</p></div>
            <div class="p-3 bg-gray-50 dark:bg-gray-800/60 rounded-lg"><strong class="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wider block mb-0.5">Language</strong><p class="text-sm font-semibold">{{ tkp.metadata.language }}</p></div>
            <div class="p-3 bg-gray-50 dark:bg-gray-800/60 rounded-lg"><strong class="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wider block mb-0.5">Total Periods</strong><p class="text-sm font-semibold">{{ tkp.metadata.total_periods }}</p></div>
            <div class="p-3 bg-gray-50 dark:bg-gray-800/60 rounded-lg"><strong class="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wider block mb-0.5">Period Duration</strong><p class="text-sm font-semibold">{{ tkp.metadata.period_duration_minutes }} min</p></div>
            <div class="p-3 bg-gray-50 dark:bg-gray-800/60 rounded-lg"><strong class="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wider block mb-0.5">Category</strong><p class="text-sm font-semibold">{{ tkp.metadata.category || 'STEM' }}</p></div>
          </div>

          <h2 class="text-lg font-semibold mb-3">Learning Objectives</h2>
          <ul class="text-sm space-y-1.5 list-disc pl-5 mb-8 text-gray-700 dark:text-gray-300">
            <li v-for="(o, idx) in tkp.knowledge_base?.learning_objectives" :key="idx">{{ o }}</li>
          </ul>

          <h2 class="text-lg font-semibold mb-3">Extracted Core Concepts</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-for="(c, idx) in tkp.knowledge_base?.concepts" :key="idx" class="p-4 border border-gray-100 dark:border-gray-800 rounded-lg bg-gray-50/70 dark:bg-gray-800/40">
              <h3 class="font-semibold text-sm text-blue-600 dark:text-blue-400 mb-1">{{ c.name }}</h3>
              <p class="text-xs text-gray-600 dark:text-gray-300 mb-2">{{ c.definition }}</p>
              <div v-if="c.examples?.length" class="text-xs text-gray-500 dark:text-gray-400">
                <strong>Examples:</strong> {{ c.examples.join(', ') }}
              </div>
            </div>
          </div>
        </div>

        <!-- Lesson Plans Tab -->
        <div v-if="activeTab === 'plans'">
          <div v-for="p in tkp.teaching_plan?.periods" :key="p.period_number" class="mb-8 p-5 border border-gray-200 dark:border-gray-800 rounded-xl bg-gray-50/50 dark:bg-gray-800/30">
            <div class="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 pb-3 mb-4">
              <h3 class="text-base font-bold text-gray-900 dark:text-gray-100">Period {{ p.period_number }}: {{ p.title }}</h3>
              <span class="text-xs font-semibold px-2.5 py-1 bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 rounded-full">{{ p.duration_minutes }} min</span>
            </div>

            <!-- Objectives & Entry Ticket -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div class="p-3.5 bg-white dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700">
                <h4 class="text-xs font-bold text-gray-500 uppercase mb-1.5">Learning Objectives</h4>
                <ul class="text-xs space-y-1 list-disc pl-4 text-gray-700 dark:text-gray-300">
                  <li v-for="obj in p.learning_objectives" :key="obj">{{ obj }}</li>
                </ul>
              </div>
              <div v-if="p.entry_ticket" class="p-3.5 bg-white dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700">
                <h4 class="text-xs font-bold text-amber-600 dark:text-amber-400 uppercase mb-1.5">🎟️ Entry Ticket (Warm-Up)</h4>
                <p class="text-xs font-medium text-gray-800 dark:text-gray-200">{{ p.entry_ticket.question }}</p>
                <p v-if="p.entry_ticket.purpose" class="text-xs text-gray-500 mt-1"><em>Purpose: {{ p.entry_ticket.purpose }}</em></p>
              </div>
            </div>

            <!-- Teacher Script -->
            <div v-if="p.teacher_script" class="mb-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700">
              <h4 class="text-xs font-bold text-blue-600 dark:text-blue-400 uppercase mb-2">🗣️ Teacher Script & Delivery Instructions</h4>
              <p class="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-line leading-relaxed">{{ p.teacher_script }}</p>
            </div>

            <!-- Blackboard Notes -->
            <div v-if="p.blackboard_notes" class="mb-4 p-4 bg-gray-900 text-green-400 rounded-lg font-mono text-xs overflow-x-auto shadow-inner">
              <h4 class="text-xs font-bold text-gray-400 uppercase mb-2 font-sans">📋 Blackboard Layout & Notes</h4>
              <pre class="whitespace-pre-wrap leading-relaxed">{{ p.blackboard_notes }}</pre>
            </div>

            <!-- Checkpoint Questions & Exit Ticket -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div v-if="p.checkpoint_questions?.length" class="p-3.5 bg-white dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700">
                <h4 class="text-xs font-bold text-indigo-600 dark:text-indigo-400 uppercase mb-2">❓ Checkpoint Questions</h4>
                <div v-for="(cq, idx) in p.checkpoint_questions" :key="idx" class="mb-2 last:mb-0 text-xs">
                  <p class="font-medium text-gray-800 dark:text-gray-200">Q: {{ cq.question }}</p>
                  <p class="text-gray-500 dark:text-gray-400 mt-0.5">A: {{ cq.expected_answer }}</p>
                </div>
              </div>
              <div v-if="p.exit_ticket" class="p-3.5 bg-white dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700">
                <h4 class="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase mb-1.5">🚪 Exit Ticket</h4>
                <p class="text-xs font-medium text-gray-800 dark:text-gray-200">{{ p.exit_ticket.question }}</p>
                <p v-if="p.exit_ticket.expected_answer" class="text-xs text-gray-500 mt-1">Expected: {{ p.exit_ticket.expected_answer }}</p>
              </div>
            </div>

            <!-- Homework & Mentor Moment -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div v-if="p.homework" class="p-3.5 bg-white dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700">
                <h4 class="text-xs font-bold text-purple-600 dark:text-purple-400 uppercase mb-1.5">📚 Homework Assignment</h4>
                <p class="text-xs text-gray-700 dark:text-gray-300 mb-1">{{ p.homework.description }}</p>
                <ul v-if="p.homework.questions?.length" class="text-xs space-y-1 list-disc pl-4 text-gray-600 dark:text-gray-400">
                  <li v-for="(hq, idx) in p.homework.questions" :key="idx">{{ hq }}</li>
                </ul>
              </div>
              <div v-if="p.mentor_moment" class="p-3.5 bg-amber-50/60 dark:bg-amber-950/30 rounded-lg border border-amber-200 dark:border-amber-900/50">
                <h4 class="text-xs font-bold text-amber-700 dark:text-amber-400 uppercase mb-1.5">🌟 Mentor Moment (Inspiration)</h4>
                <p class="text-xs text-gray-700 dark:text-gray-300 italic mb-1">"{{ p.mentor_moment.anecdote }}"</p>
                <p class="text-xs text-amber-800 dark:text-amber-300 font-medium">Connection: {{ p.mentor_moment.connection_to_topic }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Assessments Tab -->
        <div v-if="activeTab === 'assessments'">
          <!-- MCQs -->
          <div class="mb-8">
            <h3 class="text-md font-bold mb-3 text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <span>Multiple Choice Questions (MCQs)</span>
              <span class="text-xs font-semibold px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full">{{ tkp.assessments?.mcqs?.length || 0 }}</span>
            </h3>
            <div class="grid grid-cols-1 gap-4">
              <div v-for="(q, i) in tkp.assessments?.mcqs" :key="i" class="p-4 bg-gray-50 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700 rounded-lg">
                <div class="flex items-start justify-between gap-2 mb-2">
                  <p class="text-sm font-semibold text-gray-900 dark:text-gray-100">{{ i + 1 }}. {{ q.question }}</p>
                  <div class="flex items-center gap-1.5 shrink-0">
                    <span :class="['text-xs px-2 py-0.5 rounded font-medium', diffCls(q.difficulty)]">{{ q.difficulty }}</span>
                    <span v-if="q.bloom_level" class="text-xs px-2 py-0.5 bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 rounded font-medium">{{ q.bloom_level }}</span>
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-2 my-2.5">
                  <div v-for="(opt, optIdx) in q.options" :key="optIdx" :class="['text-xs p-2 rounded border', opt.startsWith(q.correct_answer) || opt === q.correct_answer ? 'bg-green-50 dark:bg-green-950/60 border-green-300 text-green-800 dark:text-green-300 font-semibold' : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300']">
                    {{ opt }}
                  </div>
                </div>
                <p v-if="q.explanation" class="text-xs text-gray-500 dark:text-gray-400 mt-1"><em>Explanation: {{ q.explanation }}</em></p>
              </div>
            </div>
          </div>

          <!-- Short Answer Questions -->
          <div v-if="tkp.assessments?.short_answers?.length" class="mb-8">
            <h3 class="text-md font-bold mb-3 text-gray-900 dark:text-gray-100">Short Answer Questions</h3>
            <div class="space-y-3">
              <div v-for="(sa, i) in tkp.assessments.short_answers" :key="i" class="p-4 bg-gray-50 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700 rounded-lg text-xs">
                <div class="flex justify-between font-semibold text-sm mb-1">
                  <span>{{ i + 1 }}. {{ sa.question }}</span>
                  <span class="text-blue-600 dark:text-blue-400">{{ sa.marks }} Marks</span>
                </div>
                <p class="text-gray-700 dark:text-gray-300 mt-1"><strong>Model Answer:</strong> {{ sa.model_answer }}</p>
                <p v-if="sa.rubric" class="text-gray-500 dark:text-gray-400 mt-1"><strong>Rubric:</strong> {{ sa.rubric }}</p>
              </div>
            </div>
          </div>

          <!-- Numerical Problems -->
          <div v-if="tkp.assessments?.numerical_problems?.length" class="mb-8">
            <h3 class="text-md font-bold mb-3 text-gray-900 dark:text-gray-100">Numerical Problems</h3>
            <div class="space-y-3">
              <div v-for="(num, i) in tkp.assessments.numerical_problems" :key="i" class="p-4 bg-gray-50 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700 rounded-lg text-xs">
                <div class="flex justify-between font-semibold text-sm mb-1">
                  <span>{{ i + 1 }}. {{ num.question }}</span>
                  <span class="text-blue-600 dark:text-blue-400">{{ num.marks }} Marks</span>
                </div>
                <p class="text-gray-700 dark:text-gray-300 mt-1"><strong>Solution Step:</strong> {{ num.solution }}</p>
                <p class="text-green-600 dark:text-green-400 font-semibold mt-1">Final Answer: {{ num.answer }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Activities Tab -->
        <div v-if="activeTab === 'activities'">
          <div v-for="period in tkp.teaching_plan?.periods" :key="period.period_number" class="mb-6">
            <h3 class="text-md font-bold mb-3 text-gray-900 dark:text-gray-100 border-b border-gray-200 dark:border-gray-700 pb-2">Period {{ period.period_number }}: {{ period.title }}</h3>
            <div v-if="!period.classroom_activities?.length" class="text-xs text-gray-400 italic">No structured activities registered for this period.</div>
            <div v-else class="grid grid-cols-1 gap-4">
              <div v-for="(act, idx) in period.classroom_activities" :key="idx" class="p-4 bg-gray-50 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700 rounded-lg">
                <div class="flex items-center justify-between mb-2">
                  <h4 class="font-bold text-sm text-blue-600 dark:text-blue-400">{{ act.title }}</h4>
                  <div class="flex items-center gap-2">
                    <span class="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 rounded font-semibold">{{ act.type }}</span>
                    <span class="text-xs text-gray-500">{{ act.duration_minutes }} min</span>
                  </div>
                </div>
                <div class="text-xs space-y-2 text-gray-700 dark:text-gray-300">
                  <p v-if="act.materials_needed?.length"><strong>Materials Needed:</strong> {{ act.materials_needed.join(', ') }}</p>
                  <p><strong>Teacher Instructions:</strong> {{ act.teacher_instructions }}</p>
                  <p v-if="act.student_instructions"><strong>Student Instructions:</strong> {{ act.student_instructions }}</p>
                  <p v-if="act.success_criteria" class="text-emerald-600 dark:text-emerald-400"><strong>Success Criteria:</strong> {{ act.success_criteria }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Learning Gaps Tab -->
        <div v-if="activeTab === 'gaps'">
          <h3 class="text-md font-bold mb-4 text-gray-900 dark:text-gray-100">Identified Learning Gaps & Remedial Strategy</h3>
          <div class="grid grid-cols-1 gap-4">
            <div v-for="g in tkp.learning_gaps" :key="g.gap_id || g.description" class="p-4 bg-gray-50 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700 rounded-lg">
              <div class="flex items-center justify-between mb-2">
                <h4 class="font-bold text-sm text-gray-900 dark:text-gray-100">{{ g.description || g.concept }}</h4>
                <span :class="['text-xs px-2.5 py-0.5 rounded-full font-semibold uppercase', sevCls(g.severity)]">{{ g.severity }} severity</span>
              </div>
              <div class="text-xs space-y-2 text-gray-700 dark:text-gray-300">
                <p v-if="g.diagnostic_question"><strong>Diagnostic Question:</strong> {{ g.diagnostic_question }}</p>
                <p v-if="g.expected_wrong_answer" class="text-red-500"><strong>Common Wrong Thought:</strong> {{ g.expected_wrong_answer }}</p>
                <p class="text-green-600 dark:text-green-400 font-medium"><strong>Remedial Action:</strong> {{ g.remedial_action }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Validation Tab -->
        <div v-if="activeTab === 'validation'">
          <h3 class="text-md font-bold mb-4 text-gray-900 dark:text-gray-100">Automated Validation Report</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div class="p-4 bg-gray-50 dark:bg-gray-800/60 rounded-lg border border-gray-200 dark:border-gray-700">
              <span class="text-xs text-gray-400 uppercase font-semibold block mb-1">Schema Adherence Status</span>
              <span :class="['text-base font-bold', tkp.validation_report?.schema_valid ? 'text-green-600' : 'text-red-600']">
                {{ tkp.validation_report?.schema_valid ? '✅ VALIDATED (Schema Compliant)' : '❌ INVALID SCHEMA' }}
              </span>
            </div>
            <div class="p-4 bg-gray-50 dark:bg-gray-800/60 rounded-lg border border-gray-200 dark:border-gray-700">
              <span class="text-xs text-gray-400 uppercase font-semibold block mb-1">Completeness Score</span>
              <span class="text-base font-bold text-blue-600 dark:text-blue-400">
                {{ ((tkp.validation_report?.completeness_score || 1.0) * 100).toFixed(0) }}%
              </span>
            </div>
          </div>

          <div v-if="tkp.validation_report?.hallucination_flags?.length" class="mb-4 p-4 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 rounded-lg">
            <h4 class="text-xs font-bold text-amber-700 dark:text-amber-400 uppercase mb-2">⚠️ Hallucination / Scope Alerts</h4>
            <ul class="text-xs space-y-1 list-disc pl-4 text-amber-800 dark:text-amber-300">
              <li v-for="(h, idx) in tkp.validation_report.hallucination_flags" :key="idx">{{ h }}</li>
            </ul>
          </div>

          <div v-if="tkp.validation_report?.consistency_issues?.length" class="p-4 bg-gray-50 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h4 class="text-xs font-bold text-gray-500 uppercase mb-2">Consistency Audit</h4>
            <ul class="text-xs space-y-1 list-disc pl-4 text-gray-600 dark:text-gray-400">
              <li v-for="(c, idx) in tkp.validation_report.consistency_issues" :key="idx">{{ c }}</li>
            </ul>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useJobsStore } from '../stores/jobs'
import LoadingSkeleton from '../components/common/LoadingSkeleton.vue'

const route = useRoute()
const router = useRouter()
const { fetchJob, removeJob } = useJobsStore()
const tkp = ref(null), loading = ref(true), activeTab = ref('overview')
const tabs = [
  { key: 'overview', label: 'Overview' },
  { key: 'plans', label: 'Lesson Plans' },
  { key: 'assessments', label: 'Assessments' },
  { key: 'activities', label: 'Activities' },
  { key: 'gaps', label: 'Gaps' },
  { key: 'validation', label: 'Validation' },
]

function tabCls(k) {
  return activeTab.value === k
    ? 'bg-blue-600 text-white shadow-sm font-semibold'
    : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
}

function diffCls(d) { return { easy: 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300', medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-300', hard: 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300' }[d] || '' }

function sevCls(s) { return { low: 'bg-green-100 text-green-700', medium: 'bg-yellow-100 text-yellow-700', high: 'bg-red-100 text-red-700' }[s] || 'bg-gray-100 text-gray-600' }

async function handleDelete() {
  if (confirm('Are you sure you want to delete this document?')) {
    await removeJob(route.params.id)
    router.push('/')
  }
}

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
