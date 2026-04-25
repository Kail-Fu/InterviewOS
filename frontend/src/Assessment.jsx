import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useForm } from 'react-hook-form';
import Navbar from "./components/ui/navbar";
import TermsAndConditions from './pages/TermsAndConditions';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const COMPANY_LANGUAGE_MAP = {
  veespark: 'zh',
  'stack auth': 'en',
  minerva: 'en',
  guard_owl: 'en',
};
const DEFAULT_LANGUAGE = 'en';

const TRANSLATIONS = {
  en: {
    assessmentTitle: 'Foretoken AI Assessment',
    nameLabel: 'Name',
    emailLabel: 'Email',
    consentLabel: 'Share your assessment results with companies for opportunities?',
    consentYes: "Yes – I'd like to be contacted",
    consentNo: 'No – Just keep it private',
    startButton: 'Start Assessment',
    startingButton: 'Starting...',
    beforeStartTitle: 'Before you start:',
    beforeStartTips: [
      'Once you start, you will be asked to share your screen.',
      'Make sure to select your entire screen, not just a window or tab.',
      'We do not recommend using Safari.',
    ],
    beforeStartFooter: 'Have fun with the assessment and do your best!',
    selectOption: 'Select an option',
    nameRequired: 'Name is required',
    emailInvalid: 'Enter a valid email',
    consentRequired: 'Please select an option',
    termsLabel: 'I agree to the',
    termsLink: 'Terms and Conditions',
    termsRequired: 'You must agree to the terms and conditions',

    // Device setup
    deviceSetupTitle: 'Check your device settings',
    cameraLabel: 'Camera',
    microphoneLabel: 'Microphone',
    screenShareLabel: 'Screen Share',
    selectCamera: 'Select Camera',
    selectMicrophone: 'Select Microphone',
    permissionRequired: 'Permission required',
    enableAccess: 'You must enable access before joining the assessment.',
    troubleshooting: 'Troubleshooting',
    troubleshootingTitle: 'Troubleshooting: Camera/Mic Permission Errors',
    troubleshootingDesc: 'Before contacting support, please try these troubleshooting steps first. Most issues can be resolved quickly by following these instructions.',
    troubleshootingSteps: [
      'Click the camera icon in your browser\'s address bar',
      'Select "Always allow" for camera and microphone',
      'Refresh the page and try again',
      'If using Chrome, go to Settings > Privacy and Security > Site Settings',
      'Ensure camera and microphone are not blocked for this site'
    ],
    stillDoesntWork: 'Still doesn\'t work',
    theseStepsWorked: 'These steps worked',
    
    // Screen share troubleshooting
    screenShareTroubleshootingTitle: 'Troubleshooting: Screen Share Permission Errors',
    screenShareTroubleshootingDesc: 'Having trouble sharing your screen? Follow these steps to resolve screen sharing issues.',
    screenShareTroubleshootingSteps: [
      'Make sure to select "Entire Screen" not "Window" or "Tab"',
      'Click "Share" or "Allow" when the browser asks for permission',
      'If you accidentally denied permission, click the screen icon in your browser\'s address bar',
      'Select "Always allow" for screen sharing',
      'Refresh the page and try again',
      'If using Chrome, go to Settings > Privacy and Security > Site Settings',
      'Ensure screen sharing is not blocked for this site'
    ],

    // New keys
    recordingInProgress: 'Screen Shared! Recording in progress...',
    zipAutoDownload: 'The assessment ZIP should download automatically. If it didn\'t, click',
    clickHere: 'here',
    downloadZip: 'and download the repo as a zip.',
    downloadLink: 'https://github.com/Kail-Fu/foretoken_swe_assessment_5',
    whatToDoNext: 'What to Do Next',
    nextSteps: [
      '📁 Open the downloaded ZIP file and follow instructions in the README.md',
      '⏳ You have 1 hour to complete the tasks',
      '🧠 Use any AI tools, but do the work solo — no second-person help',
      '📩 At the end, you will be asked to record a reflection video and submit your work.',
    ],
    needHelp: 'Something wrong? Please contact who sent you this assessment.',
    uploadingRecording: 'Uploading your recording. Please wait...',
    prepareReflection: 'Prepare for Reflection',
    uploadingReflection: 'Uploading your reflection...',
    doNotCloseWindow: 'Please do not close this window.',
    submitZipInstruction: 'Please compress your code directory and submit the code (.zip)',
    uploading: 'Uploading...',
    uploadZip: 'Upload ZIP',
    uploadSuccess: 'Upload successful!',

    reflection: {
      getReady: 'Get Ready',
      speakPrompt: "You'll be asked to speak for up to",
      minutes: '2 minutes',
      onFollowing: 'on the following:',
      topics: [
        'What problem were you solving?',
        'How did you approach the challenge?',
        'What would you do next with more time?',
      ],
      whatToTalk: 'What to Talk About',
      startNow: 'Start Recording Now',
      recordingBeginsIn: 'Recording begins in:',
      timeLeft: 'Time left:',
      endRecording: 'End Recording Early',
      nextSection: 'Next Question',
      sectionProgress: 'Question {current} of {total}',
    },
  },

  zh: {
    assessmentTitle: 'Foretoken AI 测试',
    nameLabel: '姓名',
    emailLabel: '电子邮箱',
    consentLabel: '是否愿意将您的测试结果分享给公司以获得机会？',
    consentYes: '是的 – 我希望被联系',
    consentNo: '不 – 请保持私密',
    startButton: '开始测试',
    startingButton: '正在启动...',
    beforeStartTitle: '开始前须知：',
    beforeStartTips: [
      '开始后，您将被要求共享屏幕。',
      '请务必选择整个屏幕，而不是窗口或标签页。',
      '我们不推荐使用 Safari 浏览器。',
    ],
    beforeStartFooter: '祝您测试顺利，发挥最佳水平！',
    selectOption: '请选择',
    nameRequired: '请输入姓名',
    emailInvalid: '请输入有效的电子邮箱地址',
    consentRequired: '请选择一个选项',
    termsLabel: '我同意',
    termsLink: '条款和条件',
    termsRequired: '您必须同意条款和条件',

    // Device setup
    deviceSetupTitle: '检查您的设备设置',
    cameraLabel: '摄像头',
    microphoneLabel: '麦克风',
    screenShareLabel: '屏幕共享',
    selectCamera: '选择摄像头',
    selectMicrophone: '选择麦克风',
    permissionRequired: '需要权限',
    enableAccess: '您必须在加入测试前启用访问权限。',
    troubleshooting: '故障排除',
    troubleshootingTitle: '故障排除：摄像头/麦克风权限错误',
    troubleshootingDesc: '在联系支持之前，请先尝试这些故障排除步骤。大多数问题可以通过遵循这些说明快速解决。',
    troubleshootingSteps: [
      '点击浏览器地址栏中的摄像头图标',
      '为摄像头和麦克风选择"始终允许"',
      '刷新页面并重试',
      '如果使用 Chrome，请转到设置 > 隐私和安全 > 网站设置',
      '确保此网站未阻止摄像头和麦克风'
    ],
    stillDoesntWork: '仍然无法工作',
    theseStepsWorked: '这些步骤有效',
    
    // Screen share troubleshooting
    screenShareTroubleshootingTitle: '故障排除：屏幕共享权限错误',
    screenShareTroubleshootingDesc: '无法共享屏幕？请按照以下步骤解决屏幕共享问题。',
    screenShareTroubleshootingSteps: [
      '确保选择"整个屏幕"而不是"窗口"或"标签页"',
      '当浏览器请求权限时，点击"共享"或"允许"',
      '如果您不小心拒绝了权限，请点击浏览器地址栏中的屏幕图标',
      '为屏幕共享选择"始终允许"',
      '刷新页面并重试',
      '如果使用 Chrome，请转到设置 > 隐私和安全 > 网站设置',
      '确保此网站未阻止屏幕共享'
    ],

    // New keys
    recordingInProgress: '屏幕已共享！正在录制中...',
    zipAutoDownload: '测试 ZIP 文件应会自动下载。如果没有，请点击',
    clickHere: '这里',
    downloadZip: '然后下载项目 zip 文件。',
    downloadLink: 'https://github.com/ForetokenAI/veespark-backend-assessment',
    whatToDoNext: '接下来请执行以下操作',
    nextSteps: [
      '📁 打开下载的 ZIP 文件，并按照 README.md 中的说明进行操作',
      '⏳您有 1 小时时间完成任务',
      '🧠 可使用任何 AI 工具，但需独立完成 —— 不可让他人协助',
      '📩 最后，您需要录制一段总结视频并提交作业',
    ],
    needHelp: '如有问题，请联系向您发送此测评的人。',
    uploadingRecording: '正在上传您的录屏，请稍候...',
    prepareReflection: '准备开始总结',
    uploadingReflection: '正在上传您的总结视频...',
    doNotCloseWindow: '请勿关闭此窗口',
    submitZipInstruction: '请将代码文件夹压缩后提交 (.zip)',
    uploading: '正在上传...',
    uploadZip: '上传 ZIP',
    uploadSuccess: '上传成功！',

    reflection: {
      getReady: '准备开始',
      speakPrompt: '请您用不超过',
      minutes: '2 分钟',
      onFollowing: '来讲述以下内容：',
      topics: [
        '您在解决什么问题？',
        '您是如何应对这个挑战的？',
        '如果有更多时间，您会接下来做什么？',
      ],
      whatToTalk: '谈些什么',
      startNow: '立即开始录制',
      recordingBeginsIn: '录制将在以下时间后开始：',
      timeLeft: '剩余时间：',
      endRecording: '提前结束录制',
      nextSection: '下一个问题',
      sectionProgress: '问题 {current} / {total}',
    },
  },
};



function Assessment( {company, assessmentId: propAssessmentId, assessmentTitle, inviteToken} ) {
  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm();

  const language = COMPANY_LANGUAGE_MAP[company?.toLowerCase?.()] || DEFAULT_LANGUAGE;
  const t = TRANSLATIONS[language];

  // use assessmentTitle if available, otherwise fallback to company-based logic
  if (assessmentTitle) {
    t.assessmentTitle = assessmentTitle;
  } else if (company?.toLowerCase?.() === 'veespark') {
    t.assessmentTitle = language === 'zh' ? 'VeeSpark 测试' : 'VeeSpark Assessment';
  } else if (company?.toLowerCase?.() === 'stack auth') {
    t.assessmentTitle = 'Stack Auth Assessment';
    // t.downloadLink = 'https://github.com/YourOrg/stackauth-assessment';
  } else if (company?.toLowerCase?.() === 'minerva') {
    t.assessmentTitle = 'Minerva Assessment';
    // t.downloadLink = 'https://github.com/YourOrg/minerva-assessment';
  } else if (company?.toLowerCase?.() === 'guard_owl') {
    t.assessmentTitle = 'Guard Owl Assessment';
    // t.downloadLink = 'https://github.com/YourOrg/guardowl-assessment';
  }

  const [submitted, setSubmitted] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [recording, setRecording] = useState(false);
  const [timeLeft, setTimeLeft] = useState(3600);
  const [recordingFinished, setRecordingFinished] = useState(false);
  const [downloadReady, setDownloadReady] = useState(false);
  const [showReflectionButton, setShowReflectionButton] = useState(false);
  const [isReflecting, setIsReflecting] = useState(false);
  const [reflectionReady, setReflectionReady] = useState(false);
  const [reflectionStream, setReflectionStream] = useState(null);
  const [reflectionTimeLeft, setReflectionTimeLeft] = useState(30);
  const [currentMode, setCurrentMode] = useState('camera'); // Track current mode for UI updates
  const reflectionVideoRef = useRef(null);
  const reflectionTimerRef = useRef(null); 
  const navigate = (path) => { window.location.href = path; };
  const [startTime, setStartTime] = useState(null);
  const [userInfo, setUserInfo] = useState({ name: '', email: '', assessmentId: ''});
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [termsError, setTermsError] = useState(false);

  // Device setup states
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [microphoneEnabled, setMicrophoneEnabled] = useState(false);
  const [availableCameras, setAvailableCameras] = useState([]);
  const [availableMicrophones, setAvailableMicrophones] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState('');
  const [selectedMicrophone, setSelectedMicrophone] = useState('');
  const [cameraStream, setCameraStream] = useState(null);
  const [microphoneStream, setMicrophoneStream] = useState(null);
  const [showTroubleshooting, setShowTroubleshooting] = useState(false);
  const [troubleshootingType, setTroubleshootingType] = useState('camera'); // 'camera' or 'screen'
  const [screenShareEnabled, setScreenShareEnabled] = useState(false);
  const screenShareStreamRef = useRef(null);
  const deviceVideoRef = useRef(null);
  const screenShareVideoRef = useRef(null);

  //state for invite data
  const [inviteData, setInviteData] = useState(null);
  const [isInvited, setIsInvited] = useState(false);
  const [isPreparingReflection, setIsPreparingReflection] = useState(false);
  const [prepTimeLeft, setPrepTimeLeft] = useState(60);
  const [isReflectionStarting, setIsReflectionStarting] = useState(false);
  const [isUploadingReflection, setIsUploadingReflection] = useState(false);
  const reflectionPrepTimerRef = useRef(null);

  // zip upload timer (5 minutes)
  const [zipUploadTimeLeft, setZipUploadTimeLeft] = useState(300);
  const zipUploadTimerRef = useRef(null);

  // multipart upload
  const [multipartUpload, setMultipartUpload] = useState(null);
  const multipartUploadRef = useRef(null);  

  // reflection section
  const [reflectionSections, setReflectionSections] = useState([]);
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [completedSections, setCompletedSections] = useState(new Set());
  const currentSectionIndexRef = useRef(0);
  const completedSectionsRef = useRef(new Set());
  const activeSectionIdRef = useRef(null);
  useEffect(() => { currentSectionIndexRef.current = currentSectionIndex; }, [currentSectionIndex]);
  useEffect(() => { completedSectionsRef.current = completedSections; }, [completedSections]);
  const isStartingSectionRef = useRef(false);

  // single mediarecorder to record sections continuously
  const sectionRecorderRef = useRef(null);
  const allSectionChunksRef = useRef([]);
  const currentStreamRef = useRef(null);
  const currentModeRef = useRef('camera');


  // single-recorder pipeline
  const reflectionCanvasRef = useRef(null);
  const canvasCtxRef = useRef(null);
  const rafRef = useRef(null);
  const camVideoElRef = useRef(typeof document !== 'undefined' ? document.createElement('video') : null);
  const screenVideoElRef = useRef(typeof document !== 'undefined' ? document.createElement('video') : null);

  // NEW: Fetch invite data when inviteToken is present
  useEffect(() => {
    const fetchInviteData = async () => {
      if (inviteToken) {
        try {
          const response = await axios.get(
            `${API_BASE_URL}/api/invite/verify?token=${inviteToken}`
          );
          if (response.data.valid && response.data.invite) {
            setInviteData(response.data.invite);
            setIsInvited(true);
            // Pre-fill the form fields
            setValue('name', response.data.invite.name || '');
            setValue('email', response.data.invite.email || '');
          }
        } catch (error) {
          console.error('Failed to fetch invite data:', error);
        }
      }
    };
    fetchInviteData();
  }, [inviteToken, setValue]);

  // load reflection sections
  useEffect(() => {
    const loadReflectionSections = async () => {
      try {
        // Fetch assessment-specific questions if assessmentId is available
        const endpoint = propAssessmentId 
          ? `${API_BASE_URL}/api/assessments/${propAssessmentId}/reflection-questions`
          : `${API_BASE_URL}/api/reflection/sections`;
        
        console.log('🔍 [Frontend] Loading reflection sections from:', endpoint);
        console.log('🔍 [Frontend] propAssessmentId:', propAssessmentId);
        
        const response = await axios.get(endpoint);
        console.log('🔍 [Frontend] Received sections:', response.data.sections);
        setReflectionSections(response.data.sections);
      } catch (error) {
        console.error('Failed to load reflection sections:', error);
        // fallback
        setReflectionSections([
          {
            id: "demo_work",
            question: "Show us a demo of your work.",
            requiresScreenShare: true,
            timeLimit: 120
          },
          {
            id: "struggles", 
            question: "Given more time, what would you implement next?",
            requiresScreenShare: false,
            timeLimit: 60
          }
        ]);
      }
    };
    loadReflectionSections();
  }, [propAssessmentId]);

    const getCurrentSection = () => {
      // return null if reflectionSections not loaded or index out of bounds
      if (currentSectionIndex < 0 || currentSectionIndex >= reflectionSections.length) {
        return null;
      }
      return reflectionSections[currentSectionIndex] || null;
    };


  async function initCanvasPipeline(cameraStream) {
    const W = 1280, H = 720;
    reflectionCanvasRef.current = document.createElement('canvas');
    reflectionCanvasRef.current.width = W;
    reflectionCanvasRef.current.height = H;
    canvasCtxRef.current = reflectionCanvasRef.current.getContext('2d');

    for (const v of [camVideoElRef.current, screenVideoElRef.current]) {
      if (!v) continue;
      v.playsInline = true;
      v.muted = true;
      v.autoplay = true;
    }

    camVideoElRef.current.srcObject = cameraStream;
    camVideoElRef.current.play().catch(()=>{});

    const draw = () => {
      const ctx = canvasCtxRef.current;
      const canvas = reflectionCanvasRef.current;
      if (!ctx || !canvas) return;

      const source =
        currentModeRef.current === 'screen' && screenVideoElRef.current?.srcObject
          ? screenVideoElRef.current
          : camVideoElRef.current;

      if (source && source.readyState >= 2) {
        ctx.fillStyle = '#000';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        const sw = source.videoWidth || W;
        const sh = source.videoHeight || H;
        const sAspect = sw / sh;
        const cAspect = W / H;
        let dw = W, dh = H, dx = 0, dy = 0;
        if (sAspect > cAspect) {
          dh = Math.round(W / sAspect);
          dy = Math.round((H - dh) / 2);
        } else {
          dw = Math.round(H * sAspect);
          dx = Math.round((W - dw) / 2);
        }
        ctx.drawImage(source, dx, dy, dw, dh);
      }

      rafRef.current = requestAnimationFrame(draw);
    };

    rafRef.current = requestAnimationFrame(draw);
    return reflectionCanvasRef.current.captureStream(30);
  }

  // switch stream source without stopping main recorder
  async function switchStreamSource(newStream, newMode) {
    console.log(`[FRONTEND] Switching stream source to ${newMode}`);
    if (reflectionVideoRef.current) {
      reflectionVideoRef.current.srcObject = newStream;
    }

    currentModeRef.current = newMode;
    setCurrentMode(newMode);

  }

  // ensure video element shows the current stream when mode changes
  useEffect(() => {
    if (isReflecting && currentMode === 'camera' && currentStreamRef.current && reflectionVideoRef.current) {
      console.log('[FRONTEND] Setting video srcObject in useEffect for camera mode');
      reflectionVideoRef.current.srcObject = currentStreamRef.current;
    }
  }, [isReflecting, currentMode]);

  const beginReflectionFlow = () => {
    if (isReflecting || isPreparingReflection || isReflectionStarting) return;
    // reset all states and refs at the beginning
    setCurrentSectionIndex(0);
    currentSectionIndexRef.current = 0;
    setCompletedSections(new Set());
    completedSectionsRef.current = new Set();
    activeSectionIdRef.current = null;
    allSectionChunksRef.current = [];
    setCurrentMode('camera');
    
    // show preparation page for the first question (same as subsequent questions)
    setIsPreparingReflection(true);
    setPrepTimeLeft(10);

    if (reflectionPrepTimerRef.current) {
      clearInterval(reflectionPrepTimerRef.current);
    }
  
    reflectionPrepTimerRef.current = setInterval(() => {
      setPrepTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(reflectionPrepTimerRef.current);
          reflectionPrepTimerRef.current = null;
          setIsPreparingReflection(false);
          startReflectionRecording();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };
  
  const isForceReloadingRef = useRef(false);

  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (isForceReloadingRef.current) return;
      if (recording || isReflecting || isPreparingReflection) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [recording, isReflecting, isPreparingReflection]);


  const mediaRecorderRef = useRef(null);
  const recordedChunksRef = useRef([]);
  const timerRef = useRef(null);

  const [zipFile, setZipFile] = useState(null);
  const [notebookFile, setNotebookFile] = useState(null); // NEW: for assessment4
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [isAssessment4, setIsAssessment4] = useState(false); // NEW: flag for assessment4
  const [videoBlob, setVideoBlob] = useState(null);
  const reflectionRecorderRef = useRef(null);

  useEffect(() => {
    return () => {
      // clean timers
      if (reflectionPrepTimerRef.current) {
        clearInterval(reflectionPrepTimerRef.current);
        reflectionPrepTimerRef.current = null;
      }
      if (reflectionTimerRef.current) {
        clearInterval(reflectionTimerRef.current);
        reflectionTimerRef.current = null;
      }
      if (zipUploadTimerRef.current) {
        clearInterval(zipUploadTimerRef.current);
        zipUploadTimerRef.current = null;
      }
      
      // stop section recorder
      if (sectionRecorderRef.current?.state === "recording") {
        sectionRecorderRef.current.stop();
      }
      
      if (currentStreamRef.current) {
        currentStreamRef.current.getTracks().forEach((t) => t.stop());
        currentStreamRef.current = null;
      }
      const s = screenVideoElRef.current?.srcObject;
      if (s) { s.getTracks().forEach(t => t.stop()); screenVideoElRef.current.srcObject = null; }
      if (rafRef.current) { cancelAnimationFrame(rafRef.current); rafRef.current = null; }
      canvasCtxRef.current = null;
      reflectionCanvasRef.current = null;
      
      // reset reflection states
      setIsReflecting(false);
      setIsPreparingReflection(false);
      setIsReflectionStarting(false);
      setIsUploadingReflection(false);
      setReflectionReady(false);
      setCurrentMode("camera");
      allSectionChunksRef.current = [];
      sectionRecorderRef.current = null;
      currentStreamRef.current = null;
    };
  }, []);

  const uploadSectionRecording = async (blob, sectionId) => {
    setIsUploadingReflection(true);
    const file = new File([blob], `reflection-${sectionId}.webm`, { type: 'video/webm' });
    let presigned;
    try {
      const res = await axios.post(
        `${API_BASE_URL}/get-presigned-upload-url`,
        {
          fileName: file.name,
          fileType: file.type,
          sectionId: sectionId,
          assessmentId: userInfo.assessmentId,
          inviteToken: inviteToken,
        }
      );
      presigned = res.data;
      if (!presigned?.url || !presigned?.s3Key) throw new Error('Missing presigned data');
    } catch (err) {
      console.error('[Reflection] Failed to get upload URL:', err);
      alert('Failed to get upload URL. Please try again.');
      setIsUploadingReflection(false);
      return false;
    }

    try {
      const uploadRes = await fetch(presigned.url, {
        method: 'PUT',
        headers: { 'Content-Type': file.type },
        body: file
      });
      if (!uploadRes.ok) throw new Error(`S3 upload failed: ${uploadRes.statusText}`);
    } catch (err) {
      console.error('[Reflection] Failed to upload to S3:', err);
      alert('Failed to upload to S3. Please try again.');
      setIsUploadingReflection(false);
      return false;
    }

    try {
      await axios.post(`${API_BASE_URL}/notify-recording-upload`, {
        s3Key: presigned.s3Key,
        name: userInfo.name,
        email: userInfo.email,
        type: 'reflection',
        assessmentId: userInfo.assessmentId,
        sectionId: sectionId,
      });
      return true;
    } catch (err) {
      console.error('[Reflection] Failed to notify backend after upload:', err);
      alert('Failed to notify backend after upload.');
      setIsUploadingReflection(false);
      return false;
    }
  };

const isFinalizingSectionRef = useRef(false);

const finalizeSectionRecording = async () => {
  if (isFinalizingSectionRef.current) {
    console.log('[FRONTEND] Already finalizing section, skipping...');
    return;
  }
  isFinalizingSectionRef.current = true;
  
  try {
    const idx = currentSectionIndexRef.current;
    if (completedSectionsRef.current.has(idx)) {
      console.log(`[FRONTEND] Section ${idx} already completed via ref, skipping upload`);
      isFinalizingSectionRef.current = false;
      return;
    }
    console.log(`[FRONTEND] Starting finalizeSectionRecording for section ${currentSectionIndex}`);
    activeSectionIdRef.current = null;
    // clear timer to prevent repeat 
    if (reflectionTimerRef.current) {
      clearInterval(reflectionTimerRef.current);
      reflectionTimerRef.current = null;
      console.log('[FRONTEND] Timer cleared to prevent duplicate calls');
    }
    // section check
    if (completedSections.has(currentSectionIndex)) {
      console.log(`[FRONTEND] Section ${currentSectionIndex} already completed, skipping upload`);
      return;
    }

    // get current section
    const currentSection = reflectionSections[currentSectionIndexRef.current] || getCurrentSection();
    if (!currentSection) {
      console.log('[FRONTEND] No current section found');
      return;
    }

    console.log(`[FRONTEND] Processing section: ${currentSection.id} (index: ${currentSectionIndex})`);

    // stop recording if active
    if (sectionRecorderRef.current && sectionRecorderRef.current.state === 'recording') {
      await new Promise(resolve => {
        const rec = sectionRecorderRef.current;

        let handled = false;
        const finish = () => {
          if (handled) return;
          handled = true;
          console.log(`[FRONTEND] Section recording stopped, total chunks: ${allSectionChunksRef.current.length}`);
          resolve();
        };

        rec.onstop = finish;

        // If ending *very* quickly, we may still have 0 chunks. Try to pull one.
        const hadNoChunks = allSectionChunksRef.current.length === 0;

        try { rec.requestData?.(); } catch (e) { /* noop */ }

        // If we had no chunks yet, give the browser a brief moment to emit dataavailable
        const delay = hadNoChunks ? 300 : 0;

        setTimeout(() => {
          // one more nudge just in case
          try { rec.requestData?.(); } catch (e) { /* noop */ }
          try { rec.stop(); } catch (e) { finish(); }
        }, delay);
      });
    }



    // (optional) brief micro-wait to ensure the final dataavailable landed
    await new Promise(r => setTimeout(r, 50));

    // create blob from chunks
    const sectionBlob = new Blob(allSectionChunksRef.current, { type: 'video/webm' });
    console.log(`[FRONTEND] Created section blob: ${sectionBlob.size} bytes from ${allSectionChunksRef.current.length} chunks`);
    
    // Stop canvas animation first
    if (rafRef.current) { 
      cancelAnimationFrame(rafRef.current); 
      rafRef.current = null;
      console.log('[FRONTEND] Canvas animation stopped');
    }
    
    // cleanup stream and canvas
    if (currentStreamRef.current) {
      currentStreamRef.current.getTracks().forEach(track => track.stop());
      currentStreamRef.current = null;
    }

    if (reflectionVideoRef.current) {
      reflectionVideoRef.current.srcObject = null;
    }
    
    const screenStream = screenVideoElRef.current?.srcObject;
    if (screenStream) {
      console.log('[FRONTEND] Stopping screen share tracks');
      screenStream.getTracks().forEach(track => {
        console.log(`[FRONTEND] Stopping screen ${track.kind} track`);
        track.stop();
      });
      if (screenVideoElRef.current) {
        screenVideoElRef.current.srcObject = null;
      }
    }
    
    if (camVideoElRef.current) {
      console.log('[FRONTEND] Clearing hidden camera video element');
      try {
        camVideoElRef.current.pause();
        camVideoElRef.current.srcObject = null;
        console.log('[FRONTEND] Hidden camera video element cleared');
      } catch (e) {
        console.log('[FRONTEND] Error clearing hidden camera video:', e);
      }
    }
    
    if (screenVideoElRef.current) {
      console.log('[FRONTEND] Clearing hidden screen video element');
      try {
        screenVideoElRef.current.pause();
        screenVideoElRef.current.srcObject = null;
        console.log('[FRONTEND] Hidden screen video element cleared');
      } catch (e) {
        console.log('[FRONTEND] Error clearing hidden screen video:', e);
      }
    }
    
    if (reflectionVideoRef.current) {
      console.log('[FRONTEND] Clearing visible video element');
      try {
        reflectionVideoRef.current.pause();
        reflectionVideoRef.current.srcObject = null;
        reflectionVideoRef.current.load();
        console.log('[FRONTEND] Visible video element cleared');
      } catch (e) {
        console.log('[FRONTEND] Error clearing visible video:', e);
      }
    } else {
      console.log('[FRONTEND] Visible video element ref is null (might be in screen mode)');
    }
    
    canvasCtxRef.current = null;
    reflectionCanvasRef.current = null;
    
    currentModeRef.current = 'camera';
    setCurrentMode('camera');
    
    console.log('[FRONTEND] Camera cleanup complete, now uploading...');
    
    const ok = await uploadSectionRecording(sectionBlob, currentSection.id);
    
    if (ok) {
      setCompletedSections(prev => {
        const next = new Set(prev);
        next.add(idx);
        completedSectionsRef.current = next;
        return next;
      });
      console.log(`[FRONTEND] Section ${idx} marked as completed`);

      
      // section indexing
      const nextSectionIndex = currentSectionIndexRef.current + 1;
      const hasMoreSections = nextSectionIndex < reflectionSections.length;
      
      console.log(`[FRONTEND] Current: ${currentSectionIndex}, Next: ${nextSectionIndex}, Total: ${reflectionSections.length}, HasMore: ${hasMoreSections}`);
      
      if (hasMoreSections) {
        console.log(`[FRONTEND] Moving to next section: ${nextSectionIndex}`);
        setCurrentSectionIndex(nextSectionIndex);
        currentSectionIndexRef.current = nextSectionIndex;

        setIsUploadingReflection(false);
        setIsReflecting(false);
        allSectionChunksRef.current = [];
        setCurrentMode('camera');
        sectionRecorderRef.current = null;        
        isStartingSectionRef.current = false;

        setIsPreparingReflection(true);
        setPrepTimeLeft(10);

        if (reflectionPrepTimerRef.current) {
          clearInterval(reflectionPrepTimerRef.current);
        }
      
        reflectionPrepTimerRef.current = setInterval(() => {
          setPrepTimeLeft((prev) => {
            if (prev <= 1) {
              clearInterval(reflectionPrepTimerRef.current);
              reflectionPrepTimerRef.current = null;
              setIsPreparingReflection(false);
              startReflectionRecording();
              return 0;
            }
            return prev - 1;
          });
        }, 1000);

      } else {
        console.log('[FRONTEND] All reflection sections completed!');        
        
        if (reflectionPrepTimerRef.current) {
          clearInterval(reflectionPrepTimerRef.current);
          reflectionPrepTimerRef.current = null;
          console.log('[FRONTEND] Cleared preparation timer');
        }
        
        if (reflectionTimerRef.current) {
          clearInterval(reflectionTimerRef.current);
          reflectionTimerRef.current = null;
          console.log('[FRONTEND] Cleared reflection timer');
        }
        
        allSectionChunksRef.current = [];
        sectionRecorderRef.current = null;
        activeSectionIdRef.current = null;
        
        setIsReflecting(false);
        setIsUploadingReflection(false);
        setIsPreparingReflection(false);
        setIsReflectionStarting(false);
        setCurrentMode('camera');
        setCurrentSectionIndex(-1);
        setReflectionReady(true);
        
        console.log('[FRONTEND] All reflection states reset, reflectionReady set to true');
        
        // 5-minute zip upload timer
        setZipUploadTimeLeft(300);
        if (zipUploadTimerRef.current) {
          clearInterval(zipUploadTimerRef.current);
        }
        zipUploadTimerRef.current = setInterval(() => {
          setZipUploadTimeLeft((prev) => {
            if (prev <= 1) {
              clearInterval(zipUploadTimerRef.current);
              zipUploadTimerRef.current = null;
              // Auto-submit when timer expires
              handleUploadZip(true);
              return 0;
            }
            return prev - 1;
          });
        }, 1000);
      }
    } else {
      console.error('[FRONTEND] Upload failed, not proceeding to next section');
    }
  } catch (error) {
    console.error('[FRONTEND] Error in finalizeSectionRecording:', error);
  } finally {
    isFinalizingSectionRef.current = false;
    console.log('[FRONTEND] finalizeSectionRecording completed, guard released');
  }
};





  const startReflectionRecording = async () => {
    if (isStartingSectionRef.current) {
      console.log('[FRONTEND] startReflectionRecording ignored (already starting)');
      return;
    }
    isStartingSectionRef.current = true;

    if (sectionRecorderRef.current?.state === 'recording') {
      console.log('[FRONTEND] Already recording, skipping startReflectionRecording');
      return;
    }    
    const sectionIndex = currentSectionIndexRef.current;
    const currentSection = reflectionSections[sectionIndex];
    
    if (!currentSection) {
      console.log(`[FRONTEND] No section found at index ${sectionIndex}`);
      return;
    }
    
    console.log(`[FRONTEND] Starting recording for section ${sectionIndex}: ${currentSection.id}`);
    activeSectionIdRef.current = currentSection.id;

    allSectionChunksRef.current = [];
    setIsReflecting(true);
    setReflectionReady(false);
    
    const timeLimit = currentSection.timeLimit || 60;
    setReflectionTimeLeft(timeLimit);

    if (reflectionTimerRef.current) {
      clearInterval(reflectionTimerRef.current);
      reflectionTimerRef.current = null;
    }

    try {
      if (currentStreamRef.current) {
        try { currentStreamRef.current.getTracks().forEach(t => t.stop()); } catch {}
        currentStreamRef.current = null;
      }
      const s = screenVideoElRef.current?.srcObject;
      if (s) {
        try { s.getTracks().forEach(t => t.stop()); } catch {}
        screenVideoElRef.current.srcObject = null;
      }
      if (reflectionVideoRef.current) {
        reflectionVideoRef.current.srcObject = null;
      }

      const cameraStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      currentStreamRef.current = cameraStream;
      currentModeRef.current = 'camera';
      setCurrentMode('camera');

      if (reflectionVideoRef.current) {
        reflectionVideoRef.current.srcObject = cameraStream;
      }
      const canvasStream = await initCanvasPipeline(cameraStream);
      const micTracks = cameraStream.getAudioTracks();
      micTracks.forEach(t => canvasStream.addTrack(t));

      const recorder = new MediaRecorder(canvasStream, { mimeType: 'video/webm;codecs=vp9,opus' });
      sectionRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => { 
        if (e.data?.size) {
          allSectionChunksRef.current.push(e.data);
        }
      };

      recorder.onerror = (err) => {
        console.error('[FRONTEND] Section MediaRecorder error:', err);
      };

      // 🔥 WARM-UP: ensure the camera <video> is actually playing and the canvas has painted
      async function waitForPlayingAndFirstFrames() {
        const v = camVideoElRef.current;
        if (v && v.readyState < 2) {
          await new Promise((resolve) => {
            const onPlay = () => { v.removeEventListener('playing', onPlay); resolve(); };
            v.addEventListener('playing', onPlay, { once: true });
            v.play().catch(() => resolve());
          });
        }
        // wait for 2 RAFs so draw() has painted at least once
        await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
      }

      await waitForPlayingAndFirstFrames();

      recorder.start(1000); // 1s chunks
      isStartingSectionRef.current = false;


      // countdown
      const tRef = { current: timeLimit };
      const sectionId = currentSection.id;
      const sectionIdx = sectionIndex;

      reflectionTimerRef.current = setInterval(() => {
        const stillSameSection = activeSectionIdRef.current === sectionId && currentSectionIndexRef.current === sectionIdx;
        const isActuallyRecording = sectionRecorderRef.current?.state === 'recording';

        if (!stillSameSection || !isActuallyRecording) {
          console.log(`[FRONTEND] Timer stopped: stillSameSection=${stillSameSection}, isRecording=${isActuallyRecording}`);
          clearInterval(reflectionTimerRef.current);
          reflectionTimerRef.current = null;
          return;
        }

        tRef.current -= 1;
        setReflectionTimeLeft(tRef.current);
        if (tRef.current <= 0) {
          clearInterval(reflectionTimerRef.current);
          reflectionTimerRef.current = null;
          if (!isFinalizingSectionRef.current) {
            console.log(`[FRONTEND] Timer expired for section ${sectionIdx}, calling finalizeSectionRecording`);
            finalizeSectionRecording();
          } else {
            console.log('[FRONTEND] Timer expired but finalization already in progress, skipping');
          }
        }
      }, 1000);
    } catch (err) {
      console.error('Reflection recording failed:', err);
      alert('Camera or microphone permission denied. Please try again.');
      setIsReflecting(false);
      isStartingSectionRef.current = false;
      if (currentStreamRef.current) {
        currentStreamRef.current.getTracks().forEach(track => track.stop());
        currentStreamRef.current = null;
      }
    }
  };

  // mode switch with no stop / start recording
  async function switchToScreenMode() {
    const currentSection = getCurrentSection();
    if (!currentSection || !currentSection.requiresScreenShare) return;
    if (currentModeRef.current === 'screen') return;

    try {
      const screen = await navigator.mediaDevices.getDisplayMedia({ video: { frameRate: 30 }, audio: false });

      // show screen in preview
      await switchStreamSource(screen, 'screen');
      screenVideoElRef.current.srcObject = screen;
      await screenVideoElRef.current.play().catch(()=>{});

      // auto return to camera if stop
      const vtrack = screen.getVideoTracks()[0];
      vtrack.addEventListener('ended', async () => {
        await switchToCameraMode();
      });
    } catch (e) {
      console.warn('User cancelled screen share or failed:', e);
    }
  }

  async function switchToCameraMode() {
    if (currentModeRef.current === 'camera') return;

    // stop only the screen preview stream; keep camera alive for mic + canvas
    const s = screenVideoElRef.current?.srcObject;
    if (s) { s.getTracks().forEach(t => t.stop()); screenVideoElRef.current.srcObject = null; }

    // restore camera in the on-screen preview
    if (reflectionVideoRef.current && currentStreamRef.current) {
      await switchStreamSource(currentStreamRef.current, 'camera');
    } else {
      currentModeRef.current = 'camera';
      setCurrentMode('camera');
    }
  }

  const handleBeginScreenShare = async () => {
    const currentSection = getCurrentSection();
    if (!currentSection || !currentSection.requiresScreenShare) return;
    if (currentMode === 'screen') return;
    await switchToScreenMode();
  };

  const handleStopScreenShare = async () => {
    if (currentMode === 'camera') return;
    await switchToCameraMode();
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.requestData();
      mediaRecorderRef.current.stop();
      setRecordingFinished(true);
    }
  
    if (startTime) {
      const durationMs = Date.now() - startTime;
      const seconds = Math.floor(durationMs / 1000);
      const h = String(Math.floor(seconds / 3600)).padStart(2, '0');
      const m = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
      const s = String(seconds % 60).padStart(2, '0');
      const totalTimeTaken = `${h}:${m}:${s}`;
      console.log("Total time taken:", totalTimeTaken);
      setUserInfo(prev => ({ ...prev, totalTimeTaken }));
    }
  
    setRecording(false);
    clearInterval(timerRef.current);
  };
  

  const formatTime = (sec) => {
    const h = String(Math.floor(sec / 3600)).padStart(2, '0');
    const m = String(Math.floor((sec % 3600) / 60)).padStart(2, '0');
    const s = String(sec % 60).padStart(2, '0');
    return `${h}:${m}:${s}`;
  };

  // resets the assessment upon error
  const resetAssessment = () => {
    isForceReloadingRef.current = true;
    try { 
      if (mediaRecorderRef.current?.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
    } catch {}

    if (timerRef.current) clearInterval(timerRef.current);
    if (reflectionTimerRef.current) clearInterval(reflectionTimerRef.current);
    if (reflectionPrepTimerRef.current) clearInterval(reflectionPrepTimerRef.current);

    setRecording(false);
    setRecordingFinished(false);
    setDownloadReady(false);
    setShowReflectionButton(false);
    setIsReflecting(false);
    setReflectionReady(false);
    setIsPreparingReflection(false);
    setIsReflectionStarting(false);
    setIsUploadingReflection(false);
    setSubmitted(false);
    setZipFile(null);
    setUploadSuccess(false);

    window.location.reload();
  };

  const startRecording = async (name, email, assessmentId) => {
    try {
      /* ───────────────────────── 1.  Capture the screen + mic ───────────────────────── */
      const screenStream = await navigator.mediaDevices.getDisplayMedia({
        video: { displaySurface: 'monitor' },
        audio: true,
        monitorTypeSurfaces: 'include',
      });

      const surface = screenStream.getVideoTracks()[0]?.getSettings()?.displaySurface;
      if (surface !== 'monitor') {
        alert('Please share your entire screen — not a window or tab.');
        screenStream.getTracks().forEach(t => t.stop());
        setSubmitted(false);
        return false;
      }

      screenStream.getVideoTracks()[0].addEventListener('ended', () => {
        if (mediaRecorderRef.current?.state === 'recording') {
          mediaRecorderRef.current.stop();
        }
        setRecording(false);
        clearInterval(timerRef.current);
      });

      let audioStream = null;
      try {
        audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch (err) {
        console.warn('Mic unavailable:', err);
      }

      const combinedStream = new MediaStream([
        ...screenStream.getVideoTracks(),
        ...screenStream.getAudioTracks(),
        ...(audioStream ? audioStream.getAudioTracks() : []),
      ]);

      /* ───────────────────────── 2.  Start multipart session ───────────────────────── */
      const { data: init } = await axios.post(
        `${API_BASE_URL}/api/recording/start-multipart-upload`,
        { name, email, assessmentId }
      );

      const uploadData = {
        uploadId: init.uploadId,
        s3Key: init.key,
        partNumber: 1,
        parts: [],
      };
      setMultipartUpload(uploadData);
      multipartUploadRef.current = uploadData;

      /* ───────────────────────── 3.  Setup MediaRecorder ───────────────────────── */
      const mediaRecorder = new MediaRecorder(combinedStream, {
        mimeType: 'video/webm;codecs=vp9,opus',
      });
      mediaRecorderRef.current = mediaRecorder;

      // Sequential upload queue
      let pendingChunks = [];
      let pendingSize = 0;
      const MIN_PART_SIZE = 10 * 1024 * 1024;
      let partUploadQueue = [];
      let isUploadingPart = false;

      async function processPartQueue() {
        if (isUploadingPart || partUploadQueue.length === 0) return;
        isUploadingPart = true;

        const { blob, partNumber } = partUploadQueue.shift();
        console.log(`📤 Uploading part ${partNumber} (${blob.size} bytes)`);

        try {
          const { data: up } = await axios.post(
            `${API_BASE_URL}/api/recording/upload-part`,
            blob,
            {
              headers: {
                'Content-Type': 'application/octet-stream',
                'x-upload-id': multipartUploadRef.current.uploadId,
                'x-part-number': partNumber,
                'x-s3-key': multipartUploadRef.current.s3Key,
              },
            }
          );
          multipartUploadRef.current.parts.push({
            ETag: up.ETag,
            PartNumber: partNumber,
          });
        } catch (err) {
          console.error(`❌ Part ${partNumber} upload failed:`, err);
        } finally {
          isUploadingPart = false;
          processPartQueue();
        }
      }

      mediaRecorder.ondataavailable = async (e) => {
        const ref = multipartUploadRef.current;
        if (e.data.size === 0 || !ref) return;

        pendingChunks.push(e.data);
        pendingSize += e.data.size;

        if (pendingSize >= MIN_PART_SIZE) {
          const combinedBlob = new Blob(pendingChunks, { type: 'video/webm' });
          const currentPartNumber = ref.partNumber;
          ref.partNumber += 1;

          partUploadQueue.push({ blob: combinedBlob, partNumber: currentPartNumber });
          processPartQueue();

          pendingChunks = [];
          pendingSize = 0;
        }
      };

      mediaRecorder.onstop = async () => {
        const ref = multipartUploadRef.current;
        if (!ref) return;

        /* flush any leftover data immediately */
        if (pendingChunks.length) {
          const blob = new Blob(pendingChunks, { type: 'video/webm' });
          const currentPartNumber = ref.partNumber;
          ref.partNumber += 1;
        
          console.log(`📤 Uploading final part ${currentPartNumber} (${blob.size} bytes)`);

          try {
            const { data: up } = await axios.post(
              `${API_BASE_URL}/api/recording/upload-part`,
              blob,
              {
                headers: {
                  'Content-Type': 'application/octet-stream',
                  'x-upload-id': ref.uploadId,
                  'x-part-number': currentPartNumber,
                  'x-s3-key': ref.s3Key,
                },
              }
            );
            // ✅ Strip quotes from ETag here to avoid CompleteMultipartUpload errors
            const cleanETag = up.ETag.replace(/"/g, '');
            ref.parts.push({ ETag: cleanETag, PartNumber: currentPartNumber });
          } catch (err) {
            console.error(`❌ Final part ${currentPartNumber} upload failed:`, err);
          }
        }

        /* stop local tracks */
        combinedStream.getTracks().forEach(t => t.stop());
        setRecording(false);
        setRecordingFinished(true);

        /* sort parts → ascending order */
        const orderedParts = [...ref.parts].sort((a, b) => a.PartNumber - b.PartNumber);

        console.log('📦 Completing upload', { ...ref, parts: orderedParts });

        try {
          await axios.post(
            `${API_BASE_URL}/api/recording/complete-multipart-upload`,
            {
              uploadId: ref.uploadId,
              key: ref.s3Key,
              parts: orderedParts,
              name,
              email,
              type: 'assessment',
              assessmentId,
            }
          );
          setDownloadReady(true);
          setShowReflectionButton(true);          
          setTimeout(() => {
            beginReflectionFlow();
          }, 100);
        } catch (err) {
          console.error('Finalize failed:', err.response?.data || err);
          alert('Failed to finalize recording upload.');
        }
      };


      mediaRecorder.start(5000); // emit every 5s
      setRecording(true);
      setStartTime(Date.now());

      /* Countdown timer */
      timerRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            clearInterval(timerRef.current);
            if (mediaRecorderRef.current?.state === 'recording') {
              mediaRecorderRef.current.requestData();
              mediaRecorderRef.current.stop();
            }
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return true;
    } catch (err) {
      console.error('Screen/audio capture failed:', err);
      alert('Screen or audio capture was denied. Please allow access and try again.');
      return false;
    }
  };

  

  useEffect(() => {
    const video = reflectionVideoRef.current;
    if (video && reflectionStream) {
      video.srcObject = reflectionStream;
      video.play().catch((err) => {
        console.warn("Autoplay prevented:", err);
      });
    }
  }, [reflectionStream]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (mediaRecorderRef.current?.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      if (reflectionTimerRef.current) {
        clearInterval(reflectionTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    return () => {
      multipartUploadRef.current = null;
    };
  }, []);

  


  // Device setup functions
  useEffect(() => {
    const initializeDevices = async () => {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const cameras = devices.filter(d => d.kind === 'videoinput');
        const mics = devices.filter(d => d.kind === 'audioinput');
        
        setAvailableCameras(cameras);
        setAvailableMicrophones(mics);
        
        if (cameras.length > 0) setSelectedCamera(cameras[0].deviceId);
        if (mics.length > 0) setSelectedMicrophone(mics[0].deviceId);
      } catch (err) {
        console.error('Failed to enumerate devices:', err);
      }
    };
    
    initializeDevices();
  }, []);

  // Auto-enable camera and microphone on page load
  useEffect(() => {
    const autoEnableDevices = async () => {
      // Wait for devices to be initialized first
      if (!selectedCamera || !selectedMicrophone) return;
      
      // Try to enable camera automatically
      try {
        const cameraStream = await navigator.mediaDevices.getUserMedia({
          video: selectedCamera ? { deviceId: { exact: selectedCamera } } : true,
          audio: false
        });
        setCameraStream(cameraStream);
        setCameraEnabled(true);
      } catch (err) {
        console.error('Failed to auto-enable camera:', err);
        setCameraEnabled(false);
      }

      // Try to enable microphone automatically
      try {
        const micStream = await navigator.mediaDevices.getUserMedia({
          video: false,
          audio: selectedMicrophone ? { deviceId: { exact: selectedMicrophone } } : true
        });
        setMicrophoneStream(micStream);
        setMicrophoneEnabled(true);
      } catch (err) {
        console.error('Failed to auto-enable microphone:', err);
        setMicrophoneEnabled(false);
      }
    };

    autoEnableDevices();
  }, [selectedCamera, selectedMicrophone]);


  // Handle camera stream assignment after video element is rendered
  useEffect(() => {
    if (cameraStream && cameraEnabled && deviceVideoRef.current && !screenShareEnabled) {
      console.log('useEffect: Assigning camera stream to video element');
      deviceVideoRef.current.srcObject = cameraStream;
      deviceVideoRef.current.muted = true;
      deviceVideoRef.current.playsInline = true;
      deviceVideoRef.current.play().catch(err => {
        console.log('Video autoplay failed:', err);
      });
    }
  }, [cameraStream, cameraEnabled, screenShareEnabled]);

  // Handle screen share stream assignment after video element is rendered
  useEffect(() => {
    if (screenShareStreamRef.current && screenShareEnabled && screenShareVideoRef.current) {
      console.log('useEffect: Assigning screen share stream to video element');
      screenShareVideoRef.current.srcObject = screenShareStreamRef.current;
      screenShareVideoRef.current.muted = true;
      screenShareVideoRef.current.playsInline = true;
      screenShareVideoRef.current.play().catch(err => {
        console.log('Screen share video autoplay failed:', err);
      });
    }
  }, [screenShareEnabled]);

  const toggleCamera = async () => {
    if (cameraEnabled) {
      // Turn off camera
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        setCameraStream(null);
      }
      setCameraEnabled(false);
      if (deviceVideoRef.current) {
        deviceVideoRef.current.srcObject = null;
      }
    } else {
      // Turn on camera
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: selectedCamera ? { deviceId: { exact: selectedCamera } } : true,
          audio: false
        });
        
        // Set stream and enabled state - useEffect will handle video element
        setCameraStream(stream);
        setCameraEnabled(true);
      } catch (err) {
        console.error('Failed to access camera:', err);
        setTroubleshootingType('camera');
        setShowTroubleshooting(true);
      }
    }
  };


  const toggleMicrophone = async () => {
    if (microphoneEnabled) {
      // Turn off microphone
      if (microphoneStream) {
        microphoneStream.getTracks().forEach(track => track.stop());
        setMicrophoneStream(null);
      }
      setMicrophoneEnabled(false);
    } else {
      // Turn on microphone
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: false,
          audio: selectedMicrophone ? { deviceId: { exact: selectedMicrophone } } : true
        });
        
        setMicrophoneStream(stream);
        setMicrophoneEnabled(true);
      } catch (err) {
        console.error('Failed to access microphone:', err);
        setTroubleshootingType('camera');
        setShowTroubleshooting(true);
      }
    }
  };

  const handleCameraChange = async (e) => {
    const newCameraId = e.target.value;
    setSelectedCamera(newCameraId);
    
    if (cameraEnabled) {
      // Restart stream with new camera
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
      
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { deviceId: { exact: newCameraId } },
          audio: false
        });
        
        setCameraStream(stream);
        
        if (deviceVideoRef.current) {
          deviceVideoRef.current.srcObject = stream;
          deviceVideoRef.current.play().catch(err => console.log('Play failed:', err));
        }
      } catch (err) {
        console.error('Failed to switch camera:', err);
      }
    }
  };


  const toggleScreenShare = async () => {
    if (screenShareEnabled) {
      // Turn off screen share
      if (screenShareStreamRef.current) {
        screenShareStreamRef.current.getTracks().forEach(track => track.stop());
        screenShareStreamRef.current = null;
      }
      setScreenShareEnabled(false);
      if (screenShareVideoRef.current) {
        screenShareVideoRef.current.srcObject = null;
      }
    } else {
      // Turn on screen share
      try {
        const stream = await navigator.mediaDevices.getDisplayMedia({
          video: { displaySurface: 'monitor' },
          audio: false
        });
        
        const videoTrack = stream.getVideoTracks()[0];
        const settings = videoTrack.getSettings();
        
        if (settings.displaySurface !== 'monitor') {
          alert('Please select "Entire Screen" for screen sharing.');
          stream.getTracks().forEach(track => track.stop());
          return;
        }
        
        screenShareStreamRef.current = stream;
        setScreenShareEnabled(true);
        
        // Auto turn off when user stops sharing
        videoTrack.onended = () => {
          setScreenShareEnabled(false);
          screenShareStreamRef.current = null;
          if (screenShareVideoRef.current) {
            screenShareVideoRef.current.srcObject = null;
          }
        };
      } catch (err) {
        console.error('Failed to access screen share:', err);
        if (err.name !== 'NotAllowedError') {
          setTroubleshootingType('camera');
        setShowTroubleshooting(true);
        }
      }
    }
  };

  const handleMicrophoneChange = async (e) => {
    const newMicId = e.target.value;
    setSelectedMicrophone(newMicId);
    
    if (microphoneEnabled) {
      if (microphoneStream) {
        microphoneStream.getTracks().forEach(track => track.stop());
      }
      
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: false,
          audio: { deviceId: { exact: newMicId } }
        });
        
        setMicrophoneStream(stream);
      } catch (err) {
        console.error('Failed to switch microphone:', err);
      }
    }
  };

  



  const cleanupDeviceStreams = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
      setCameraStream(null);
    }
    if (microphoneStream) {
      microphoneStream.getTracks().forEach(track => track.stop());
      setMicrophoneStream(null);
    }
    if (screenShareStreamRef.current) {
      screenShareStreamRef.current.getTracks().forEach(track => track.stop());
      screenShareStreamRef.current = null;
    }
    setCameraEnabled(false);
    setMicrophoneEnabled(false);
    setScreenShareEnabled(false);
    if (deviceVideoRef.current) {
      deviceVideoRef.current.srcObject = null;
    }
  };

  const onSubmit = async (data) => {
    const { name, email, shareConsent } = data;

    if (!termsAccepted) {
      setTermsError(true);
      return;
    }
    setTermsError(false);

    if (isStarting) return;
    setIsStarting(true);

    try {
      // Clean up device test streams first
      cleanupDeviceStreams();

      // NOW start assessment
      const res = await axios.post(
        `${API_BASE_URL}/start-assessment`,
        { name, email, shareConsent, company, assessmentId: propAssessmentId }
      );

      const { downloadUrl, assessmentId, assessmentType, s3Key } = res.data;
      console.log('[FRONTEND] Assessment started:', { assessmentId, assessmentType, s3Key });

      if (assessmentType === 'assessment4-ner') {
        setIsAssessment4(true);
      }

      if (downloadUrl && assessmentId) {
        setUserInfo({ name, email, assessmentId, shareConsent: company ? 'unavailable' : shareConsent, s3Key });
        setSubmitted(true);
        
        if (inviteToken) {
          try {
            await axios.post(`${API_BASE_URL}/api/invite/mark-taken`, { token: inviteToken });
          } catch (err) {
            console.error('Failed to mark invite as taken:', err);
          }
        }

        
        const recordingSuccess = await startRecording(name, email, assessmentId);
        if(recordingSuccess) {
          const link = document.createElement('a');
          link.href = downloadUrl;
          link.download = '';
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        }
      }
    } catch (err) {
      console.error('❌ Submit error:', err);
      alert('Something went wrong. Please try again later.');
      setIsStarting(false);
      setSubmitted(false);
    }
  };

  
  const handleZipChange = (e) => {
    const file = e.target.files[0];
    const validZipTypes = ['application/zip', 'application/x-zip-compressed'];
    
    if (file && validZipTypes.includes(file.type)) {
      setZipFile(file);
    } else if (file && file.name.endsWith('.zip')) {
      // Fallback in case MIME type is empty or unrecognized
      setZipFile(file);
    } else {
      alert('Please upload a valid ZIP file.');
    }
  };

  const handleNotebookChange = (e) => {
    const file = e.target.files[0];
    if (file && file.name.endsWith('.ipynb')) {
      setNotebookFile(file);
    } else {
      alert('Please upload a valid Jupyter Notebook file (.ipynb).');
    }
  };  

  const handleUploadZip = async (isAutoSubmit = false) => {
    // For assessment4, require both files
    if (isAssessment4) {
      if (!zipFile || !notebookFile) {
        if (!isAutoSubmit) {
          alert('Please upload both submission.zip and notebook.ipynb files.');
        }
        return;
      }
    } else {
      // For other assessments, only require zip
      if (!zipFile && !isAutoSubmit) return;
    }

    const formData = new FormData();
    
    if (isAssessment4) {
      // Assessment 4: dual file upload
      formData.append('submissionZip', zipFile);
      formData.append('notebookFile', notebookFile);
      formData.append('assessmentId', userInfo.assessmentId);
    } else {
      // Other assessments: single zip upload
      if (zipFile) {
        formData.append('zipFile', zipFile);
      }
      formData.append('name', userInfo.name);
      formData.append('email', userInfo.email);
      formData.append('assessmentId', userInfo.assessmentId);
    }
    
    if (company === undefined || company === null || company === '') {
      company = 'sample';
    }

    try {
      setUploading(true);
      setUploadProgress(0);
      setUploadSuccess(false);
      
      // Clear zip upload timer
      if (zipUploadTimerRef.current) {
        clearInterval(zipUploadTimerRef.current);
        zipUploadTimerRef.current = null;
      }
      
      const endpoint = isAssessment4 ? '/upload-assessment4' : '/upload-zip';
      const uploadResponse = await axios.post(`${API_BASE_URL}${endpoint}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
          console.log(`Upload progress: ${percentCompleted}%`);
        },
      });
      console.log('Upload success');
      setUploadSuccess(true);
      const reportTarget = uploadResponse?.data?.reportId || uploadResponse?.data?.candidateId || userInfo.assessmentId;
      navigate(`/${company}/loading/${reportTarget}`);
      

    } catch (err) {
      console.error('❌ Upload failed:', err);
      if (isAutoSubmit) {
        // For auto-submit, just navigate anyway since time is up
        console.log('Auto-submit proceeding despite upload error');
        navigate(`/${company}/loading/${userInfo.assessmentId}`);
      } else {
        alert('Failed to upload file. Please try again.');
      }
    } finally {
      setUploading(false);
    }
  };

  // visuals
  const pageBgStyle = {
    background:
      "radial-gradient(1100px 620px at 50% -180px, rgba(0,0,0,0.10), rgba(0,0,0,0) 60%)," +
      "linear-gradient(180deg, #ffffff 0%, #f6f6f6 55%, #efefef 100%)",
  };

  const chromeLight = {
    background:
      "radial-gradient(120% 60% at 50% -20%, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0) 55%)," +
      "linear-gradient(180deg, #ffffff 0%, #f7f7f7 100%)",
    border: "1px solid rgba(0,0,0,0.06)",
    boxShadow: "0 6px 14px rgba(0,0,0,0.06)",
  };

  const lightCardBL = {
    ...chromeLight,
    borderRadius: "22px",
  };

  const primaryBtn =
    "relative overflow-hidden group bg-black text-white font-medium py-3 px-6 rounded-xl transition-all duration-200 hover:bg-gray-900 hover:shadow-lg hover:shadow-black/20 active:scale-[0.98]";

  const primaryBtnShine =
    "absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/25 to-transparent transition-transform duration-700 ease-out group-hover:translate-x-full";

  // current section for display
  const currentSection = getCurrentSection();
  const sectionProgress = reflectionSections.length > 0 
    ? t.reflection.sectionProgress
        .replace('{current}', (currentSectionIndex + 1).toString())
        .replace('{total}', reflectionSections.length.toString())
    : '';

  // debug state
  const debugState = {
    isReflecting,
    reflectionReady,
    isUploadingReflection,
    isPreparingReflection,
    isReflectionStarting,
    currentSectionIndex,
    currentSection: getCurrentSection(),
    completedSections: Array.from(completedSections),
    showReflectionButton,
    recordingFinished,
    downloadReady
  };

  console.log('[FRONTEND] Render state:', debugState);

  return (
    <div className="relative min-h-screen text-black isolate">
      <div aria-hidden className="pointer-events-none fixed inset-0 z-0" style={pageBgStyle} />
      <div className="relative z-10">
        <div className="fixed top-0 left-0 w-full z-50 bg-white/80 backdrop-blur border-b border-black/5">
          <Navbar showAuth={false} showDemo={false} />
        </div>
        <section className="relative w-full px-6 md:px-20 pt-[9.5rem] pb-16">
          <div className="max-w-3xl mx-auto">
            
            <div
              className="rounded-[22px] overflow-hidden p-8 sm:p-10"
              style={lightCardBL}
            >
              <h2 className="text-2xl md:text-3xl font-bold text-black text-center mb-6">
                {t.assessmentTitle}
              </h2>

              {submitted ? (
                <div className="space-y-5 text-center">
                  {recording && (
                    <p className="text-emerald-700 font-medium px-5">
                      ✅ {t.recordingInProgress}
                      <br />
                      {/* <span className="text-sm text-gray-700">
                        {t.zipAutoDownload}{" "}
                        <a
                          href={t.downloadLink}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline"
                        >
                          {t.clickHere}
                        </a>{" "}
                        {t.downloadZip}
                      </span> */}
                      <span className="text-sm text-gray-700">
                        The assessment ZIP should download automatically. If it didn't, click{" "}
                        <button
                          onClick={async () => {
                            try {
                              const res = await axios.post(`${API_BASE_URL}/download-assessment`, {
                                company,
                                assessmentId: propAssessmentId,
                              });
                              const presignedUrl = res.data?.downloadUrl;
                              if (presignedUrl) {
                                const link = document.createElement("a");
                                link.href = presignedUrl;
                                link.target = "_blank";
                                link.rel = "noopener noreferrer";
                                document.body.appendChild(link);
                                link.click();
                                document.body.removeChild(link);
                              } else {
                                alert("No download link found.");
                              }
                            } catch (err) {
                              console.error("Failed to fetch assessment zip:", err);
                              alert("Download failed. Please try again later.");
                            }
                          }}
                          className="text-blue-600 hover:underline underline-offset-2"
                          style={{ padding: 0, border: "none", background: "none", cursor: "pointer" }}
                        >
                          here
                        </button>{" "}
                        to manually trigger the download. If blocked, please allow downloads or pop-ups for this site and try again.
                        {/* Only show GitHub link for default assessment.zip */}
                        {userInfo?.s3Key === 'assessment.zip' && (
                          <>
                            <br />
                            Reference repo:{" "}
                            <a
                              href={t.downloadLink}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:underline"
                            >
                              GitHub
                            </a>
                          </>
                        )}
                      </span>
                    </p>
                  )}

                  {recording && (
                    <>
                      <div className="text-black text-lg font-mono">
                        {t.reflection.timeLeft} {formatTime(timeLeft)}
                      </div>

                      <div className="mt-2 text-left space-y-3 bg-white/70 p-4 rounded-xl border border-black/10 text-gray-800 text-sm">
                        <h3 className="text-base font-semibold text-black">📋 {t.whatToDoNext}</h3>
                        <ul className="list-disc list-inside space-y-1">
                          {t.nextSteps.map((item, idx) => (
                            <li key={idx}>{item}</li>
                          ))}
                        </ul>
                        <div className="pt-3 border-t border-black/10">
                          ❓ {t.needHelp}
                        </div>
                      </div>

                      <button
                        onClick={stopRecording}
                        disabled={!recording}
                        className="mt-2 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {t.reflection.endRecording}
                      </button>
                    </>
                  )}

                  {recordingFinished && !downloadReady && (
                    <p className="text-amber-600 text-center font-medium mt-2">
                      ⏳ {t.uploadingRecording}
                    </p>
                  )}



                  {isReflecting && !isUploadingReflection && !reflectionReady && currentSection && currentSectionIndex >= 0 && currentSectionIndex < reflectionSections.length && (
                    <div className="mt-4 flex flex-col items-center space-y-4">
                      {/* section Progress */}
                      <div className="text-sm font-medium text-gray-600 mb-2">
                        {sectionProgress}
                      </div>
                      
                      {/* current Question */}
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4 w-full">
                        <h3 className="text-lg font-semibold text-blue-900 mb-2">
                          Question {currentSectionIndex + 1}:
                        </h3>
                        <p className="text-blue-800">{currentSection.question}</p>
                        <div className="text-sm text-blue-600 mt-2">
                          Time limit: {Math.floor((currentSection.timeLimit || 120) / 60)} minutes
                          {currentSection.requiresScreenShare && (
                            <span className="ml-2 bg-blue-100 px-2 py-1 rounded text-xs">
                              Screen sharing available
                            </span>
                          )}
                        </div>
                      </div>

                      {/* timer */}
                      <div className="text-black text-lg font-mono mb-4">
                        {t.reflection.timeLeft} {formatTime(reflectionTimeLeft)}
                      </div>

                      <video 
                        ref={reflectionVideoRef} 
                        autoPlay 
                        muted 
                        playsInline 
                        className="w-full max-w-md rounded-lg shadow-lg"
                        style={{ display: 'block' }}
                      />
                      <div className="flex justify-center space-x-4">
                        {currentSection.requiresScreenShare && (
                          <>
                            {currentMode === 'camera' ? (
                              <button
                                onClick={handleBeginScreenShare}
                                className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition"
                              >
                                Share Screen
                              </button>
                            ) : (
                              <button
                                onClick={handleStopScreenShare}
                                className="bg-orange-600 hover:bg-orange-700 text-white font-medium py-2 px-4 rounded-lg transition"
                              >
                                Stop Sharing
                              </button>
                            )}
                          </>
                        )}
                        <button
                          onClick={() => {
                            console.log('[FRONTEND] Button clicked, calling finalizeSectionRecording');
                            finalizeSectionRecording();
                          }}
                          disabled={isFinalizingSectionRef.current}
                          className="bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {currentSectionIndex < reflectionSections.length - 1 
                            ? t.reflection.nextSection 
                            : t.reflection.endRecording}
                        </button>
                      </div>
                    </div>
                  )}

                  {isUploadingReflection && (
                    <div className="bg-white p-6 rounded-2xl border border-black/10 shadow-sm text-gray-800 text-center">
                      <p className="text-lg font-semibold">⏳ {t.uploadingReflection}</p>
                      <p className="text-sm text-gray-600 mt-2">{t.doNotCloseWindow}</p>
                      {currentSection && (
                        <p className="text-sm text-gray-500 mt-1">
                          Processing question {currentSectionIndex + 1} of {reflectionSections.length}
                        </p>
                      )}
                    </div>
                  )}

                  {isPreparingReflection && currentSection && (
                    <div className="bg-white p-6 rounded-2xl border border-black/10 shadow-sm text-gray-800 space-y-6 text-center">
                      <h2 className="text-2xl font-bold text-black flex items-center justify-center gap-2">
                        <span role="img" aria-label="mic">
                          🎤
                        </span>{" "}
                        {t.reflection.getReady}
                      </h2>
                      
                      {/* section Progress */}
                      <div className="text-sm font-medium text-gray-600">
                        {sectionProgress}
                      </div>

                      {/* current Question */}
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <h3 className="text-lg font-semibold text-blue-900 mb-2">
                          Question {currentSectionIndex + 1}:
                        </h3>
                        <p className="text-blue-800">{currentSection.question}</p>
                        <div className="text-sm text-blue-600 mt-2">
                          Time limit: {Math.floor((currentSection.timeLimit || 120) / 60)} minutes
                          {currentSection.requiresScreenShare && (
                            <span className="ml-2 bg-blue-100 px-2 py-1 rounded text-xs">
                              Screen sharing available
                            </span>
                          )}
                        </div>
                      </div>

                      {/* <p className="text-base">
                        {t.reflection.speakPrompt} <strong>{Math.floor((currentSection.timeLimit || 120) / 60)} {t.reflection.minutes}</strong>{" "}
                        {t.reflection.onFollowing}
                      </p> */}

                      <p className="font-mono text-gray-800 text-lg">
                        {t.reflection.recordingBeginsIn} {formatTime(prepTimeLeft)}
                      </p>

                      <button
                        onClick={async () => {
                          if (isReflecting || isReflectionStarting) return;
                          setIsPreparingReflection(false);
                          setIsReflectionStarting(true);
                          await startReflectionRecording();
                          setIsReflectionStarting(false);
                        }}
                        className={primaryBtn}
                      >
                        <span className="relative z-10">{t.reflection.startNow}</span>
                        <span className={primaryBtnShine} />
                      </button>

                      <div className="text-xs text-gray-600 pt-4 border-t border-black/10">
                        {t.needHelp}
                      </div>
                    </div>
                  )}

                  {reflectionReady && (
                    <div className="mt-4 space-y-4 text-center">
                      <p className="text-black font-medium">
                        {isAssessment4 
                          ? 'Please upload your submission.zip and notebook.ipynb files' 
                          : t.submitZipInstruction}
                      </p>
                      <div className="text-red-600 font-mono text-lg font-bold">
                        Time remaining: {formatTime(zipUploadTimeLeft)}
                      </div>
                      <p className="text-sm text-gray-600">
                        You have 5 minutes to upload your submission. If time expires, it will auto-submit.
                      </p>
                      
                      {isAssessment4 ? (
                        // Assessment 4: Dual file upload
                        <>
                          <div className="space-y-2">
                            <label className="block text-left text-sm font-medium text-gray-700">
                              1. Upload submission.zip (trained model)
                            </label>
                            <input
                              type="file"
                              accept=".zip"
                              onChange={handleZipChange}
                              className="w-full text-sm text-gray-800 file:bg-black file:text-white file:rounded-lg file:px-4 file:py-2 file:cursor-pointer file:border file:border-black/80 file:shadow-[inset_0_0_0_1px_rgba(255,255,255,.08)]"
                            />
                            {zipFile && (
                              <p className="text-xs text-green-600 text-left">✓ {zipFile.name}</p>
                            )}
                          </div>
                          
                          <div className="space-y-2">
                            <label className="block text-left text-sm font-medium text-gray-700">
                              2. Upload notebook.ipynb (your Jupyter Notebook)
                            </label>
                            <input
                              type="file"
                              accept=".ipynb"
                              onChange={handleNotebookChange}
                              className="w-full text-sm text-gray-800 file:bg-black file:text-white file:rounded-lg file:px-4 file:py-2 file:cursor-pointer file:border file:border-black/80 file:shadow-[inset_0_0_0_1px_rgba(255,255,255,.08)]"
                            />
                            {notebookFile && (
                              <p className="text-xs text-green-600 text-left">✓ {notebookFile.name}</p>
                            )}
                          </div>
                        </>
                      ) : (
                        // Other assessments: Single zip upload
                        <input
                          type="file"
                          accept=".zip"
                          onChange={handleZipChange}
                          className="w-full text-sm text-gray-800 file:bg-black file:text-white file:rounded-lg file:px-4 file:py-2 file:cursor-pointer file:border file:border-black/80 file:shadow-[inset_0_0_0_1px_rgba(255,255,255,.08)]"
                        />
                      )}
                      
                      {/* Upload Button with Built-in Progress Bar */}
                      <div className="space-y-2">
                        <button
                          onClick={handleUploadZip}
                          disabled={(isAssessment4 ? (!zipFile || !notebookFile) : !zipFile) || uploading}
                          className="relative overflow-hidden w-full font-medium py-3 px-6 rounded-xl transition-all duration-200 disabled:opacity-50 border border-black/10"
                          style={{
                            background: uploading 
                              ? `linear-gradient(to right, #000000 ${uploadProgress}%, #f3f3f3 ${uploadProgress}%)`
                              : '#000000'
                          }}
                        >
                          <span 
                            className="relative z-10 transition-colors duration-200"
                            style={{ 
                              color: uploading && uploadProgress > 50 ? '#ffffff' : uploading ? '#000000' : '#ffffff'
                            }}
                          >
                            {uploading ? `${t.uploading} ${uploadProgress}%` : t.uploadZip}
                          </span>
                          {!uploading && (
                            <span className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/25 to-transparent transition-transform duration-700 ease-out group-hover:translate-x-full" />
                          )}
                        </button>
                        
                        {uploadSuccess && (
                          <p className="text-emerald-700 text-center font-medium">{t.uploadSuccess}</p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <>

                  <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                  <div className="space-y-4 mb-2">
                    {/* Name */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        {t.nameLabel}
                      </label>
                      <input
                        {...register("name", { required: true, maxLength: 120 })}
                        placeholder="Your full name"
                        className="w-full px-4 py-2 bg-white border border-black/10 text-black rounded-lg focus:outline-none focus:ring-2 focus:ring-black/50"
                      />
                      {errors.name && (
                        <p className="text-red-600 text-sm mt-1">{t.nameRequired}</p>
                      )}
                    </div>

                    {/* Email */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        {t.emailLabel}
                      </label>
                      <input
                        {...register("email", {
                          required: true,
                          pattern: /^\S+@\S+$/i,
                        })}
                        placeholder="you@example.com"
                        className="w-full px-4 py-2 bg-white border border-black/10 text-black rounded-lg focus:outline-none focus:ring-2 focus:ring-black/50"
                      />
                      {errors.email && (
                        <p className="text-red-600 text-sm mt-1">{t.emailInvalid}</p>
                      )}
                    </div>

                    {/* Consent */}
                    {!company && !inviteToken && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          {t.consentLabel}
                        </label>
                        <div className="relative">
                          <select
                            {...register("shareConsent", { required: true })}
                            className="block w-full appearance-none bg-white border border-black/10 text-black px-4 py-2 pr-10 rounded-lg focus:outline-none focus:ring-2 focus:ring-black/50 text-sm"
                          >
                            <option value="">{t.selectOption}</option>
                            <option value="yes">{t.consentYes}</option>
                            <option value="no">{t.consentNo}</option>
                          </select>
                          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
                            <svg
                              className="h-4 w-4 text-gray-500"
                              xmlns="http://www.w3.org/2000/svg"
                              viewBox="0 0 20 20"
                              fill="currentColor"
                            >
                              <path
                                fillRule="evenodd"
                                d="M10 12a1 1 0 01-.707-.293l-4-4a1 1 0 111.414-1.414L10 9.586l3.293-3.293a1 1 0 011.414 1.414l-4 4A1 1 0 0110 12z"
                                clipRule="evenodd"
                              />
                            </svg>
                          </div>
                        </div>
                        {errors.shareConsent && (
                          <p className="text-red-600 text-sm mt-1">{t.consentRequired}</p>
                        )}
                      </div>
                    )}
                  </div>


                  {/* Device Setup Section */}
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-700">{t.deviceSetupTitle}</h3>
                      <button
                        type="button"
                        onClick={() => setShowTroubleshooting(true)}
                        className="text-sm text-blue-600 hover:text-blue-800 underline"
                      >
                        {t.troubleshooting}
                      </button>
                    </div>
                    
                    {/* Camera/Screen Share Preview */}
                    <div className="mb-4">
                      <div className="bg-black rounded-lg overflow-hidden mb-3 w-full max-w-md mx-auto" style={{ aspectRatio: '16/9', position: 'relative' }}>
                        {screenShareEnabled ? (
                          <video
                            ref={screenShareVideoRef}
                            autoPlay
                            playsInline
                            muted
                            className="w-full h-full object-contain"
                          />
                        ) : cameraEnabled ? (
                          <video
                            ref={deviceVideoRef}
                            autoPlay
                            playsInline
                            muted
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex flex-col items-center justify-center text-white">
                            <svg className="w-16 h-16 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                            <p className="text-sm">{t.permissionRequired}</p>
                            <p className="text-xs text-gray-400 mt-1">{t.enableAccess}</p>
                          </div>
                        )}
                        
                        {/* Toggle buttons overlay */}
                        {(!cameraEnabled || !microphoneEnabled) && (
                          <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-3">
                            {!cameraEnabled && (
                              <button
                                type="button"
                                onClick={toggleCamera}
                                className="w-12 h-12 rounded-full flex items-center justify-center transition-all bg-red-600 text-white hover:bg-red-700"
                                title="Enable Camera"
                              >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                  <line x1="2" y1="2" x2="22" y2="22" strokeWidth={2} strokeLinecap="round"/>
                                </svg>
                              </button>
                            )}
                            
                            {/* Microphone Toggle - only show if disabled */}
                            {!microphoneEnabled && (
                              <button
                                type="button"
                                onClick={toggleMicrophone}
                                className="w-12 h-12 rounded-full flex items-center justify-center transition-all bg-red-600 text-white hover:bg-red-700"
                                title="Enable Microphone"
                              >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                                  <line x1="2" y1="2" x2="22" y2="22" strokeWidth={2} strokeLinecap="round"/>
                                </svg>
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Device Selection Dropdowns */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      {/* Camera Selection */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          {t.cameraLabel}
                        </label>
                        <select
                          value={selectedCamera}
                          onChange={handleCameraChange}
                          className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-black/50"
                        >
                          {availableCameras.map((camera) => (
                            <option key={camera.deviceId} value={camera.deviceId}>
                              {camera.label || `Camera ${camera.deviceId.substring(0, 5)}`}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Microphone Selection */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          {t.microphoneLabel}
                        </label>
                        <select
                          value={selectedMicrophone}
                          onChange={handleMicrophoneChange}
                          className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-black/50"
                        >
                          {availableMicrophones.map((mic) => (
                            <option key={mic.deviceId} value={mic.deviceId}>
                              {mic.label || `Microphone ${mic.deviceId.substring(0, 5)}`}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                  </div>

                  {/* Terms and Conditions Checkbox */}
                  <div className={termsError ? "border-2 border-red-500 rounded-lg p-3 bg-red-50" : ""}>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={termsAccepted}
                        onChange={(e) => {
                          setTermsAccepted(e.target.checked);
                          if (e.target.checked) setTermsError(false);
                        }}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">
                        {t.termsLabel}{' '}
                        <button
                          type="button"
                          onClick={() => setShowTermsModal(true)}
                          className="text-blue-600 hover:text-blue-800 underline font-medium"
                        >
                          {t.termsLink}
                        </button>
                      </span>
                    </label>
                    {termsError && (
                      <p className="text-red-600 text-sm mt-2 font-semibold flex items-center gap-1">
                        <span>{t.termsRequired}</span>
                      </p>
                    )}
                  </div>

                  {/* Info note */}
                  <div className="text-sm text-gray-800 bg-white/70 border border-black/10 rounded-md p-4">
                    <p className="mb-1 font-medium text黑">{t.beforeStartTitle}</p>
                    <ul className="list-disc list-inside space-y-1">
                      {t.beforeStartTips.map((tip, idx) => (
                        <li key={idx}>{tip}</li>
                      ))}
                    </ul>
                    <p className="mt-2">{t.beforeStartFooter}</p>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-3">
                    <button 
                      type="submit" 
                      className={`${primaryBtn} w-full`}
                      disabled={isStarting}
                      style={isStarting ? { opacity: 0.6, cursor: 'not-allowed' } : {}}
                    >
                      <span className="relative z-10">{isStarting ? t.startingButton : t.startButton}</span>
                      <span className={primaryBtnShine} />
                    </button>
                  </div>
                </form>
                </>
              )}
            </div>

          </div>
        </section>
      </div>
      
      {/* Troubleshooting Modal */}
      {showTroubleshooting && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full p-8 shadow-2xl">
            {/* Header */}
            <div className="mb-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-4 flex-1 pr-4">
                  <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-7 h-7 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      {troubleshootingType === 'camera' ? (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      ) : (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      )}
                    </svg>
                  </div>
                  <h3 className="text-xl md:text-2xl font-bold text-gray-900 leading-snug">
                    {troubleshootingType === 'camera' ? t.troubleshootingTitle : t.screenShareTroubleshootingTitle}
                  </h3>
                </div>
                <button
                  onClick={() => setShowTroubleshooting(false)}
                  className="text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            {/* Description */}
            <p className="text-base text-gray-600 mb-6 leading-relaxed">
              {troubleshootingType === 'camera' ? t.troubleshootingDesc : t.screenShareTroubleshootingDesc}
            </p>
            
            {/* Steps */}
            <div className="mb-8">
              <p className="font-semibold text-lg mb-4 text-gray-900">Follow these steps:</p>
              <ol className="space-y-3">
                {(troubleshootingType === 'camera' ? t.troubleshootingSteps : t.screenShareTroubleshootingSteps).map((step, idx) => (
                  <li key={idx} className="flex gap-4 text-gray-700">
                    <span className="font-bold text-lg text-gray-900 flex-shrink-0">{idx + 1}.</span>
                    <span className="text-base leading-relaxed pt-0.5">{step}</span>
                  </li>
                ))}
              </ol>
            </div>
            
            {/* Action Buttons */}
            <div className="flex gap-4">
              <button
                onClick={() => setShowTroubleshooting(false)}
                className="flex-1 bg-gray-100 text-gray-800 py-3 px-6 rounded-lg font-semibold hover:bg-gray-200 transition-colors text-base"
              >
                {t.stillDoesntWork}
              </button>
              <button
                onClick={() => setShowTroubleshooting(false)}
                className="flex-1 bg-black text-white py-3 px-6 rounded-lg font-semibold hover:bg-gray-800 transition-colors text-base"
              >
                {t.theseStepsWorked}
              </button>
            </div>
          </div>
        </div>
      )}
      
{/* Terms and Conditions Modal */}
      {showTermsModal && (
        <TermsAndConditions onClose={() => setShowTermsModal(false)} />
      )}
    </div>
  );
}

export default Assessment;
