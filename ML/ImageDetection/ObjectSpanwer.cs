#if UNITY_EDITOR
using UnityEditor;
using System.IO;
#endif

using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using System.Linq;

public class DatasetGenerator : MonoBehaviour
{
    [Header("Prefabs")]
    public GameObject[] carModels;
    public GameObject[] noiseObjects;

    [Header("Counts")]
    public int carCount = 10;
    public int generateCount = 100;

    [Header("Placement")]
    public float minGap = 2.0f;
    public float margin = 0.1f;
    public float carRadius = 1.0f;

    [Header("Appearance")]
    public float recolorRate = 0.5f;

    [Header("Capture")]
    public Camera captureCamera;
    public int captureWidth = 1920;
    public int captureHeight = 1080;
    [Range(1,100)] public int jpgQuality = 90;

    [Header("IO")]
    public string imagesDir = "datasets/dota/images/train";
    public string labelsDir = "datasets/dota/labels/train";

    // pooling
    private readonly Dictionary<GameObject, Queue<GameObject>> pools = new();
    private readonly Dictionary<GameObject, GameObject> active = new();
    private Transform poolParent;

    void Awake()
    {
        Application.runInBackground = true;
        if (!captureCamera) captureCamera = Camera.main;
        InitPools();
    }

    void InitPools()
    {
        poolParent = new GameObject("ObjectPool").transform;
        poolParent.SetParent(transform);
        if (carModels != null)
            foreach (var pf in carModels.Where(p => p))
                Prewarm(pf, carCount * 2);
        if (noiseObjects != null)
            foreach (var pf in noiseObjects.Where(p => p))
                Prewarm(pf, 20);
    }

    void Prewarm(GameObject prefab, int count)
    {
        pools[prefab] = new Queue<GameObject>();
        for (int i=0;i<count;i++)
        {
            var o = Instantiate(prefab, poolParent);
            o.SetActive(false);
            pools[prefab].Enqueue(o);
        }
    }

    GameObject Get(GameObject prefab)
    {
        if (!pools.ContainsKey(prefab)) pools[prefab] = new Queue<GameObject>();
        var o = pools[prefab].Count>0 ? pools[prefab].Dequeue() : Instantiate(prefab);
        o.SetActive(true);
        active[o] = prefab;
        return o;
    }

    void Put(GameObject o)
    {
        if (!active.TryGetValue(o, out var pf)) { Destroy(o); return; }
        o.SetActive(false);
        o.transform.SetParent(poolParent);
        pools[pf].Enqueue(o);
        active.Remove(o);
    }

    void PutAll()
    {
        foreach (var o in active.Keys.ToArray()) Put(o);
    }

    void Start()
    {
        if (carModels == null || carModels.Length == 0)
        {
            Debug.LogError("carModels를 채워주세요.");
            return;
        }
        Directory.CreateDirectory(imagesDir);
        Directory.CreateDirectory(labelsDir);
        StartCoroutine(GenerateDataset());
    }

    IEnumerator GenerateDataset()
    {
        for (int i=0;i<generateCount;i++)
        {
            var cars = SpawnCars();

            string stem = $"img{(i+1):D4}";
            string imgPath = Path.Combine(imagesDir,  stem + ".jpg");
            string txtPath = Path.Combine(labelsDir,  stem + ".txt");

            yield return CaptureAndLabel(cars, captureCamera, imgPath, txtPath, captureWidth, captureHeight, jpgQuality);

            foreach (var c in cars) Put(c);
            yield return null;
        }
        Debug.Log("데이터셋 생성 완료");
        PutAll();
    }

    IEnumerator CaptureAndLabel(List<GameObject> cars, Camera cam,
                            string imgPath, string txtPath,
                            int W, int H, int quality)
    {
        var rt  = new RenderTexture(W, H, 24) { antiAliasing = 1 };
        var tex = new Texture2D(W, H, TextureFormat.RGB24, false);

        cam.targetTexture = rt;

        // 1) RT 기준으로 렌더 → 라벨 산출(정규화 W,H 동일)
        cam.Render();
        SaveOBBLabels(cars, cam, txtPath, W, H);

        // 2) 같은 RT에서 픽셀 읽어 저장
        RenderTexture.active = rt;
        tex.ReadPixels(new Rect(0, 0, W, H), 0, 0);
        tex.Apply();
        System.IO.File.WriteAllBytes(imgPath, tex.EncodeToJPG(quality));

        // 3) 정리
        cam.targetTexture = null;
        RenderTexture.active = null;
        Destroy(rt);
        Destroy(tex);
        yield return null;
    }

    List<GameObject> SpawnCars()
    {
        var cam = captureCamera ? captureCamera : Camera.main;
        float y = 0f;

        Vector3 left = cam.ViewportToWorldPoint(new Vector3(0.05f, 0, 11f));
        Vector3 right = cam.ViewportToWorldPoint(new Vector3(0.95f, 0, 11f));
        float worldMinX = Mathf.Min(left.x, right.x);
        float worldMaxX = Mathf.Max(left.x, right.x);

        Vector3 near = cam.ViewportToWorldPoint(new Vector3(0, 0, 11f));
        Vector3 far  = cam.ViewportToWorldPoint(new Vector3(0, 1, 11f));
        float worldMinZ = Mathf.Min(near.z, far.z);
        float worldMaxZ = Mathf.Max(near.z, far.z);

        var positions = new List<Vector3>();
        var spawned = new List<GameObject>();
        int maxTry = 200;

        for (int i=0;i<carCount;i++)
        {
            float minX = worldMinX + carRadius + margin;
            float maxX = worldMaxX - carRadius - margin;
            float minZ = worldMinZ + carRadius + margin;
            float maxZ = worldMaxZ - carRadius - margin;

            bool found=false; int tries=0; Vector3 pos=Vector3.zero;
            while (!found && tries++ < maxTry)
            {
                pos = new Vector3(Random.Range(minX,maxX), y, Random.Range(minZ,maxZ));
                bool overlap=false;
                foreach (var p in positions)
                    if (Vector3.Distance(p, pos) < carRadius*2f + minGap) { overlap=true; break; }
                if (!overlap) { positions.Add(pos); found=true; }
            }
            if (!found) continue;

            int idx = Random.Range(0, carModels.Length);
            var car = Get(carModels[idx]);
            car.transform.position = pos;
            car.transform.rotation = Quaternion.Euler(0, Random.Range(-30f,30f), 0);

            if (Random.value < recolorRate)
            {
                var col = Random.ColorHSV(0f,1f, 0.6f,1f, 0.7f,1f);
                foreach (var r in car.GetComponentsInChildren<MeshRenderer>())
                    foreach (var m in r.materials) m.color = col;
            }
            spawned.Add(car);
        }
        return spawned;
    }

    // ─ Capture with RenderTexture ─
    IEnumerator Capture(Camera cam, string path, int W, int H, int quality)
    {
        var rt = new RenderTexture(W, H, 24) { antiAliasing = 1 };
        var tex = new Texture2D(W, H, TextureFormat.RGB24, false);

        cam.targetTexture = rt;
        cam.Render();                    // 즉시 1프레임 렌더
        RenderTexture.active = rt;
        tex.ReadPixels(new Rect(0,0,W,H), 0, 0);
        tex.Apply();

        File.WriteAllBytes(path, tex.EncodeToJPG(quality));

        cam.targetTexture = null;
        RenderTexture.active = null;
        Destroy(rt);
        Destroy(tex);
        yield return null;               // 프레임 양보
    }

    // ─ Labels: Mesh → 2D → Hull → ForceRect(직각 강제) ─
    void SaveOBBLabels(List<GameObject> cars, Camera cam, string labelPath, int W, int H)
    {
        var lines = new List<string>();

        // RT 크기와 동일하게 보정
        if (cam.targetTexture != null) { W = cam.targetTexture.width; H = cam.targetTexture.height; }

        foreach (var car in cars)
        {
            var pts = ProjectMesh2D(car, cam, W, H);
            if (pts.Count < 3) continue;

            var hull = ConvexHull2D(pts.ToArray());
            var rect = ForceRectFromHull(hull);   // ← 변경: PCA 기반 직각 강제
            rect = OrderCWStartTopLeft(rect);

            string line = "0";
            for (int i = 0; i < 4; i++)
                line += $" {rect[i].x:F6} {rect[i].y:F6}";
            lines.Add(line);
        }
        File.WriteAllLines(labelPath, lines);
    }

    // PCA 기반으로 항상 직각이 되는 최소외접사각형
    Vector2[] ForceRectFromHull(IList<Vector2> hull)
    {
        // 중심 계산
        float cx = 0, cy = 0;
        foreach (var p in hull) { cx += p.x; cy += p.y; }
        cx /= hull.Count; cy /= hull.Count;

        // 공분산 행렬 요소
        float sxx = 0, sxy = 0, syy = 0;
        foreach (var p in hull)
        {
            float x = p.x - cx, y = p.y - cy;
            sxx += x * x;
            sxy += x * y;
            syy += y * y;
        }

        // 주축 각도
        float t = sxx - syy;
        float r = Mathf.Atan2(2f * sxy, t) * 0.5f;
        Vector2 u = new(Mathf.Cos(r), Mathf.Sin(r));   // 주축
        Vector2 v = new(-u.y, u.x);                    // 직교축

        // 투영 범위
        float uMin = +1e9f, uMax = -1e9f, vMin = +1e9f, vMax = -1e9f;
        foreach (var p in hull)
        {
            float du = Vector2.Dot(new Vector2(p.x - cx, p.y - cy), u);
            float dv = Vector2.Dot(new Vector2(p.x - cx, p.y - cy), v);
            if (du < uMin) uMin = du; if (du > uMax) uMax = du;
            if (dv < vMin) vMin = dv; if (dv > vMax) vMax = dv;
        }

        // 꼭짓점 생성 (항상 직각)
        Vector2 P(float du, float dv) => new(cx + du * u.x + dv * v.x,
                                            cy + du * u.y + dv * v.y);
        var rect = new Vector2[4];
        rect[0] = P(uMin, vMin);
        rect[1] = P(uMax, vMin);
        rect[2] = P(uMax, vMax);
        rect[3] = P(uMin, vMax);
        return rect;
    }

    // ... 나머지 코드는 기존과 동일 ...


    List<Vector2> ProjectMesh2D(GameObject go, Camera cam, int W, int H)
    {
        var pts = new List<Vector2>(2048);

        // MeshFilter (정적 메시)
        foreach (var mf in go.GetComponentsInChildren<MeshFilter>())
        {
            var mesh = mf.sharedMesh; if (!mesh) continue;
            if (!mesh.isReadable) { Debug.LogWarning($"Unreadable Mesh: {mesh.name} on {mf.name}"); continue; }

            var l2w = mf.transform.localToWorldMatrix;
            foreach (var v in mesh.vertices)
            {
                var sp = cam.WorldToScreenPoint(l2w.MultiplyPoint3x4(v));
                if (sp.z <= 0) continue;
                var p = new Vector2(sp.x / W, 1f - sp.y / H);
                pts.Add(new Vector2(Mathf.Clamp01(p.x), Mathf.Clamp01(p.y)));
            }
        }

        // SkinnedMeshRenderer (스키닝 메시)
        foreach (var smr in go.GetComponentsInChildren<SkinnedMeshRenderer>())
        {
            if (!smr.sharedMesh) continue;
            using (var tmp = new TempMesh())
            {
                smr.BakeMesh(tmp.Mesh, true);
                var l2w = smr.transform.localToWorldMatrix;
                foreach (var v in tmp.Mesh.vertices)
                {
                    var sp = cam.WorldToScreenPoint(l2w.MultiplyPoint3x4(v));
                    if (sp.z <= 0) continue;
                    var p = new Vector2(sp.x / W, 1f - sp.y / H);
                    pts.Add(new Vector2(Mathf.Clamp01(p.x), Mathf.Clamp01(p.y)));
                }
            }
        }
        return pts;
    }

    sealed class TempMesh : System.IDisposable
    {
        public Mesh Mesh { get; }
        public TempMesh(){ Mesh = new Mesh(); Mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32; }
        public void Dispose(){ if (Application.isPlaying) Object.Destroy(Mesh); else Object.DestroyImmediate(Mesh); }
    }


    Vector2[] ConvexHull2D(Vector2[] pts)
    {
        if (pts.Length <= 3) return pts.ToArray();
        var sorted = pts.OrderBy(p=>p.x).ThenBy(p=>p.y).ToArray();
        List<Vector2> lower = new(), upper = new();

        foreach (var p in sorted)
        {
            while (lower.Count >= 2 && Cross(lower[^2], lower[^1], p) <= 0) lower.RemoveAt(lower.Count-1);
            lower.Add(p);
        }
        for (int i = sorted.Length-1; i>=0; i--)
        {
            var p = sorted[i];
            while (upper.Count >= 2 && Cross(upper[^2], upper[^1], p) <= 0) upper.RemoveAt(upper.Count-1);
            upper.Add(p);
        }
        lower.RemoveAt(lower.Count-1);
        upper.RemoveAt(upper.Count-1);
        lower.AddRange(upper);
        return lower.ToArray();
    }

    float Cross(Vector2 o, Vector2 a, Vector2 b) => (a.x-o.x)*(b.y-o.y) - (a.y-o.y)*(b.x-o.x);

    Vector2[] MinAreaRectFromHull(IList<Vector2> hull)
    {
        int n = hull.Count;
        if (n < 3) return hull.ToArray();

        float best = float.MaxValue;
        Vector2[] bestRect = new Vector2[4];

        for (int i=0;i<n;i++)
        {
            Vector2 o = hull[i];
            Vector2 e = hull[(i+1)%n] - o;
            float ang = Mathf.Atan2(e.y, e.x);
            float cos = Mathf.Cos(-ang), sin = Mathf.Sin(-ang);

            float minX=float.PositiveInfinity, maxX=float.NegativeInfinity;
            float minY=float.PositiveInfinity, maxY=float.NegativeInfinity;

            for (int k=0;k<n;k++)
            {
                Vector2 p = hull[k] - o;
                float rx = cos*p.x - sin*p.y;
                float ry = sin*p.x + cos*p.y;
                if (rx < minX) minX = rx; if (rx > maxX) maxX = rx;
                if (ry < minY) minY = ry; if (ry > maxY) maxY = ry;
            }

            float area = (maxX-minX)*(maxY-minY);
            if (area < best)
            {
                best = area;
                float cr = Mathf.Cos(ang), sr = Mathf.Sin(ang);
                Vector2 R(float x, float y) => new Vector2(cr*x - sr*y, sr*x + cr*y) + o;
                bestRect[0] = R(minX, minY);
                bestRect[1] = R(maxX, minY);
                bestRect[2] = R(maxX, maxY);
                bestRect[3] = R(minX, maxY);
            }
        }
        return bestRect;
    }

    Vector2[] OrderCWStartTopLeft(Vector2[] pts)
    {
        // CW로 맞추기
        float area = 0f;
        for (int i=0;i<4;i++)
        {
            var a = pts[i]; var b = pts[(i+1)%4];
            area += (a.x*b.y - a.y*b.x);
        }
        if (area > 0) System.Array.Reverse(pts); // CCW면 뒤집기

        // 좌상단(start) 고정
        int s = 0;
        for (int i=1;i<4;i++)
            if (pts[i].y < pts[s].y || (Mathf.Approximately(pts[i].y, pts[s].y) && pts[i].x < pts[s].x))
                s = i;

        var outPts = new Vector2[4];
        for (int i=0;i<4;i++) outPts[i] = pts[(s+i)%4];
        return outPts;
    }

    #if UNITY_EDITOR

    public void Editor_EnableReadWriteForCarModels()
    {
        if (carModels == null || carModels.Length == 0)
        {
            Debug.LogWarning("carModels 비어있음");
            return;
        }

        var paths = new HashSet<string>();
        foreach (var prefab in carModels)
        {
            if (!prefab) continue;

            foreach (var mf in prefab.GetComponentsInChildren<MeshFilter>(true))
            {
                var mesh = mf.sharedMesh; if (!mesh) continue;
                var p = AssetDatabase.GetAssetPath(mesh);
                if (!string.IsNullOrEmpty(p)) paths.Add(p);
            }
            foreach (var smr in prefab.GetComponentsInChildren<SkinnedMeshRenderer>(true))
            {
                var mesh = smr.sharedMesh; if (!mesh) continue;
                var p = AssetDatabase.GetAssetPath(mesh);
                if (!string.IsNullOrEmpty(p)) paths.Add(p);
            }
        }

        Directory.CreateDirectory("Assets/Imported"); // Packages→Assets 복사용

        int enabled = 0, skipped = 0, copied = 0, pkg = 0;
        foreach (var path in paths)
        {
            string usePath = path;

            // Packages 경로는 임포트 설정을 못 바꿈 → Assets로 복사
            if (path.StartsWith("Packages/"))
            {
                pkg++;
                var dst = $"Assets/Imported/{Path.GetFileName(path)}";
                if (AssetDatabase.CopyAsset(path, dst))
                {
                    usePath = dst;
                    copied++;
                }
                else
                {
                    Debug.LogWarning($"Copy failed: {path}");
                    continue;
                }
            }

            var importer = AssetImporter.GetAtPath(usePath) as ModelImporter;
            if (importer == null) { skipped++; continue; }

            if (!importer.isReadable)
            {
                importer.isReadable = true;
                importer.SaveAndReimport();
                enabled++;
            }
            else skipped++;
        }

        Debug.Log($"Read/Write enabled: {enabled}, skipped: {skipped}, copied: {copied}, packagesFound: {pkg}");
        Debug.LogWarning("Packages에서 복사된 모델은 Assets/Imported에 있습니다. 필요하면 프리팹의 메쉬 참조를 복사본으로 바꿔주세요.");
    }
    #endif

}

