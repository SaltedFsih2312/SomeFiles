import re, sys, os

Options = sys.argv[1]
ImageList = "calico/apiserver calico/cni calico/kube-controllers calico/node calico/typha calico/pod2daemon-flexvol tigera/key-cert-provisioner tigera/operator calico/csi".split(' ')

match Options:
    case '0':
        InputImages = sys.argv[2:]
        SelectImages = [k for i in ImageList for k in InputImages if re.search(i, k) != None and re.search('-fips|windows', k) == None]
        for i in SelectImages:
            print(i)

    case '1':
        InputImages = sys.argv[2:]
        SelectImages = [k for i in ImageList for k in InputImages if re.search(i, k) != None and re.search('-fips|windows', k) == None]
        InResNodeImages = []
        for ImageURL in SelectImages:
            ImagePath = '/'.join(ImageURL.split('/')[1:])
            InResNodeImages.append("ResNode.k8s.exam/"+ImagePath)
        for ImageURL in InResNodeImages:
            # command = r"\$\(docker inspect {} -f '\{\{range .RepoDigests\}\}\{\{printf '\%\s' .\}\}\{\{end\}\}'\)".format(ImageURL)
            command = "docker inspect " + ImageURL +" -f '{{range .RepoDigests}}{{printf \"%s\" .}}{{end}}'"
            os.system("python3.11 UseCalicoImages.py 2 {} $({})".format(ImageURL, command))

    case '2':
        Digests = sys.argv[3].split('@')
        Image = '/'.join(sys.argv[2].split(':')[0].split('/')[1:])
        print(f"- image: {Image}")
        # print(f"  digest: \"@{Digests[1]}\"")
        print(f"  digest: {Digests[1]}")

    case _:
        print("Must In 0 or 1, In sys.argv[1]")
        exit()
